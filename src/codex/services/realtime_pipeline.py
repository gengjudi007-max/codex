from __future__ import annotations

from typing import Any, Dict, List

from codex.services.autonomous_intelligence import run_autonomous_intelligence
from codex.services.connectors import connector_items_to_sources, run_connectors
from codex.services.knowledge_graph_store import rebuild_knowledge_graph
from codex.services.newsroom_desk import build_assignments, build_morning_brief, build_topic_pool
from codex.services.newsroom_orchestrator import run_newsroom_orchestrator
from codex.services.reliability import log_event, safe_step, summarize_steps
from codex.services.source_ingestion import ingest_sources
from codex.services.sqlite_store import DEFAULT_DB_PATH, save_alerts, save_memory_events, save_run_log, save_sources


def run_realtime_pipeline(config: Dict[str, Any]) -> Dict[str, Any]:
    """Run the real-time newsroom pipeline once.

    Flow:
    connectors -> ingestion -> persistence -> orchestrator -> graph -> autonomous intelligence -> desk package.
    """
    db_path = str(config.get("db_path") or DEFAULT_DB_PATH)
    memory_path = str(config.get("memory_path") or "data/memory_events.jsonl")
    store_path = str(config.get("store_path") or "data/source_items.jsonl")
    steps: Dict[str, Dict[str, Any]] = {}

    log_event("realtime_pipeline", "pipeline started", {"db_path": db_path})

    steps["connectors"] = safe_step("connectors", lambda: run_connectors(config))
    connector_result = steps["connectors"].get("result") or {}
    connector_items = connector_items_to_sources(connector_result)

    ingestion_payload = {
        "items": list(config.get("items", [])) + connector_items,
        "texts": config.get("texts", []),
        "paths": config.get("paths", []),
        "sources": config.get("sources", []),
        "store_path": store_path,
        "memory_path": memory_path,
    }

    steps["ingestion"] = safe_step("ingestion", lambda: ingest_sources(ingestion_payload))
    ingestion = steps["ingestion"].get("result") or {}
    items = ingestion.get("items", [])

    steps["persist_sources"] = safe_step("persist_sources", lambda: save_sources(items, db_path=db_path))
    memory_events = ingestion.get("memory", {}).get("events", [])
    steps["persist_memory"] = safe_step("persist_memory", lambda: save_memory_events(memory_events, db_path=db_path))

    orchestrator_payload = {
        "items": items,
        "memory_path": memory_path,
        "previous_policy": config.get("previous_policy", ""),
        "current_policy": config.get("current_policy", ""),
    }
    if items:
        steps["orchestrator"] = safe_step("orchestrator", lambda: run_newsroom_orchestrator(orchestrator_payload))
    else:
        steps["orchestrator"] = {"name": "orchestrator", "status": "skipped", "result": None, "reason": "no_items"}
    orchestrator = steps["orchestrator"].get("result")

    steps["knowledge_graph"] = safe_step("knowledge_graph", lambda: rebuild_knowledge_graph(db_path=db_path))
    steps["autonomous_intelligence"] = safe_step("autonomous_intelligence", lambda: run_autonomous_intelligence(db_path=db_path))
    intelligence = steps["autonomous_intelligence"].get("result") or {}

    alerts = _pipeline_alerts(connector_result, ingestion, orchestrator, intelligence)
    steps["persist_alerts"] = safe_step("persist_alerts", lambda: save_alerts(alerts, source="realtime_pipeline", db_path=db_path))

    result = {
        "mode": "realtime_newsroom_pipeline",
        "summary": summarize_steps(steps),
        "steps": steps,
        "connector_summary": _connector_summary(connector_result),
        "ingestion_summary": _ingestion_summary(ingestion),
        "orchestrator_summary": _orchestrator_summary(orchestrator),
        "autonomous_intelligence": intelligence,
        "alerts": alerts,
        "desk_package": _desk_package(orchestrator, alerts),
        "claim_boundary": "实时 pipeline 生成新闻信号、预警和派单建议；事实结论仍需核验原始来源。",
    }

    steps["persist_run_log"] = safe_step("persist_run_log", lambda: save_run_log(result, db_path=db_path))
    result["summary"] = summarize_steps(steps)

    log_event("realtime_pipeline", "pipeline finished", {"summary": result["summary"]})
    return result


def _pipeline_alerts(
    connector_result: Dict[str, Any],
    ingestion: Dict[str, Any],
    orchestrator: Dict[str, Any] | None,
    intelligence: Dict[str, Any],
) -> List[str]:
    alerts: List[str] = []
    if connector_result.get("error_count", 0):
        alerts.append("实时连接器存在失败源，请检查 URL、权限、反爬或网络。")
    changed = [item for item in connector_result.get("items", []) if item.get("change", {}).get("changed")]
    if changed:
        alerts.append(f"发现 {len(changed)} 个连接器内容变化。")
    if ingestion.get("accepted_count", 0):
        alerts.append(f"本轮入库 {ingestion.get('accepted_count')} 条信息。")
    if orchestrator and orchestrator.get("reporting_package", {}).get("lead_topic"):
        alerts.append(f"触发选题：{orchestrator['reporting_package']['lead_topic']}")
    for warning in intelligence.get("early_warnings", []):
        alerts.append(warning)
    return alerts or ["本轮实时 pipeline 未发现强信号。"]


def _connector_summary(connector_result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "connector_count": connector_result.get("connector_count", 0),
        "success_count": connector_result.get("success_count", 0),
        "error_count": connector_result.get("error_count", 0),
        "changed_count": sum(1 for item in connector_result.get("items", []) if item.get("change", {}).get("changed")),
    }


def _ingestion_summary(ingestion: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "accepted_count": ingestion.get("accepted_count", 0),
        "error_count": ingestion.get("error_count", 0),
        "source_types": sorted({item.get("source_type") for item in ingestion.get("items", []) if item.get("source_type")}),
    }


def _orchestrator_summary(orchestrator: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if not orchestrator:
        return None
    return {
        "lead_topic": orchestrator.get("reporting_package", {}).get("lead_topic"),
        "risk_nodes": orchestrator.get("reporting_package", {}).get("risk_nodes", []),
        "next_actions": orchestrator.get("next_actions", []),
    }


def _desk_package(orchestrator: Dict[str, Any] | None, alerts: List[str]) -> Dict[str, Any]:
    run_result = {
        "ingestion": {"accepted_count": 0, "error_count": 0, "source_types": []},
        "orchestrator": _orchestrator_summary(orchestrator) or {},
        "alerts": alerts,
    }
    morning = build_morning_brief(run_result)
    topics = build_topic_pool(run_result)
    return {"morning_brief": morning, "topic_pool": topics, "assignments": build_assignments(topics)}
