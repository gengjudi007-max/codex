from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from codex.services.newsroom_orchestrator import run_newsroom_orchestrator
from codex.services.reliability import log_event, safe_step, summarize_steps
from codex.services.source_ingestion import ingest_sources

DEFAULT_WATCHLIST_PATH = "config/watchlist.json"
DEFAULT_RUN_LOG_PATH = "data/run_logs/continuous_runner.jsonl"


def run_once(config_path: str = DEFAULT_WATCHLIST_PATH) -> Dict[str, Any]:
    log_event("continuous_runner", "run_once started", {"config_path": config_path})

    config = load_watchlist(config_path)

    ingestion_payload = {
        "sources": config.get("sources", []),
        "texts": config.get("texts", []),
        "items": config.get("items", []),
        "paths": config.get("paths", []),
        "store_path": config.get("store_path", "data/source_items.jsonl"),
        "memory_path": config.get("memory_path", "data/memory_events.jsonl"),
        "timeout": config.get("timeout", 15),
    }

    steps: Dict[str, Dict[str, Any]] = {}

    steps["ingestion"] = safe_step(
        "ingestion",
        lambda: ingest_sources(ingestion_payload),
    )

    ingestion = steps["ingestion"].get("result") or {}

    orchestrator_payload = {
        "items": ingestion.get("items", []),
        "memory_path": config.get("memory_path", "data/memory_events.jsonl"),
        "previous_policy": config.get("previous_policy", ""),
        "current_policy": config.get("current_policy", ""),
    }

    if ingestion.get("items"):
        steps["orchestrator"] = safe_step(
            "orchestrator",
            lambda: run_newsroom_orchestrator(orchestrator_payload),
        )
    else:
        steps["orchestrator"] = {
            "name": "orchestrator",
            "status": "skipped",
            "result": None,
            "reason": "no_items",
        }

    orchestrator = steps["orchestrator"].get("result")

    result = {
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "config_path": config_path,
        "steps": steps,
        "summary": summarize_steps(steps),
        "ingestion": _compact_ingestion(ingestion),
        "orchestrator": _compact_orchestrator(orchestrator),
        "alerts": _alerts(ingestion, orchestrator),
    }

    append_run_log(result, config.get("run_log_path", DEFAULT_RUN_LOG_PATH))

    log_event(
        "continuous_runner",
        "run_once finished",
        {"summary": result["summary"]},
    )

    return result


def run_loop(
    config_path: str = DEFAULT_WATCHLIST_PATH,
    interval_seconds: int | None = None,
    max_runs: int | None = None,
) -> List[Dict[str, Any]]:
    config = load_watchlist(config_path)
    interval = int(interval_seconds or config.get("interval_seconds", 3600))
    runs = []
    count = 0

    log_event(
        "continuous_runner",
        "run_loop started",
        {"interval_seconds": interval, "max_runs": max_runs},
    )

    while max_runs is None or count < max_runs:
        runs.append(run_once(config_path))
        count += 1
        if max_runs is not None and count >= max_runs:
            break
        time.sleep(interval)

    log_event(
        "continuous_runner",
        "run_loop finished",
        {"runs": len(runs)},
    )

    return runs


def load_watchlist(config_path: str = DEFAULT_WATCHLIST_PATH) -> Dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        return {
            "sources": [],
            "texts": [],
            "items": [],
            "paths": [],
            "interval_seconds": 3600,
            "store_path": "data/source_items.jsonl",
            "memory_path": "data/memory_events.jsonl",
            "run_log_path": DEFAULT_RUN_LOG_PATH,
        }
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def append_run_log(result: Dict[str, Any], log_path: str = DEFAULT_RUN_LOG_PATH) -> None:
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(result, ensure_ascii=False) + "\n")


def _compact_ingestion(ingestion: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "accepted_count": ingestion.get("accepted_count", 0),
        "error_count": ingestion.get("error_count", 0),
        "errors": ingestion.get("errors", [])[:5],
        "source_types": sorted({item.get("source_type") for item in ingestion.get("items", []) if item.get("source_type")}),
    }


def _compact_orchestrator(orchestrator: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if not orchestrator:
        return None
    topics = orchestrator.get("topics", {}).get("topics", [])
    return {
        "input_count": orchestrator.get("input_count", 0),
        "lead_topic": orchestrator.get("reporting_package", {}).get("lead_topic"),
        "topic_count": len(topics),
        "risk_nodes": orchestrator.get("reporting_package", {}).get("risk_nodes", []),
        "next_actions": orchestrator.get("next_actions", []),
    }


def _alerts(ingestion: Dict[str, Any], orchestrator: Dict[str, Any] | None) -> List[str]:
    alerts = []
    if ingestion.get("error_count", 0):
        alerts.append("存在采集失败数据源，请检查 URL、权限、反爬或文件路径。")
    if orchestrator and orchestrator.get("reporting_package", {}).get("lead_topic"):
        alerts.append("发现可推进选题。")
    risk_nodes = orchestrator.get("reporting_package", {}).get("risk_nodes", []) if orchestrator else []
    if risk_nodes:
        alerts.append("发现风险链信号：" + "、".join(risk_nodes[:5]))
    if not alerts:
        alerts.append("本轮未发现强信号。")
    return alerts
