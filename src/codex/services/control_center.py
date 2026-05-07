from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from codex.services.autonomous_intelligence import run_autonomous_intelligence
from codex.services.health_check import run_health_check
from codex.services.knowledge_graph_store import knowledge_graph_summary
from codex.services.retrieval_engine import alerts_query, claims_query, newsroom_summary
from codex.services.sqlite_store import DEFAULT_DB_PATH, db_summary

DEFAULT_RUN_LOG_PATH = "data/run_logs/continuous_runner.jsonl"
DEFAULT_ASYNC_LOG_PATH = "data/run_logs/async_runtime.jsonl"
DEFAULT_EVENT_LOG_PATH = "data/run_logs/events.jsonl"


def build_control_center(
    db_path: str = DEFAULT_DB_PATH,
    config_path: str = "config/watchlist.json",
) -> Dict[str, Any]:
    """Build a live newsroom control-center payload for dashboard/CLI use."""
    health = run_health_check(config_path)
    db = db_summary(db_path)
    newsroom = newsroom_summary(db_path)
    graph = knowledge_graph_summary(db_path)
    alerts = alerts_query(db_path, limit=20)
    risky_claims = _risky_claims(db_path)
    intelligence = run_autonomous_intelligence(db_path)
    runtime = runtime_monitor()

    return {
        "mode": "live_newsroom_control_center",
        "status": _overall_status(health, intelligence, runtime, risky_claims),
        "health": health,
        "database": db,
        "newsroom_summary": newsroom,
        "knowledge_graph": graph,
        "runtime_monitor": runtime,
        "alert_center": alerts,
        "risky_claims": risky_claims,
        "autonomous_intelligence": {
            "early_warnings": intelligence.get("early_warnings", []),
            "suggestions": intelligence.get("investigation_suggestions", []),
            "anomaly_count": len(intelligence.get("anomalies", [])),
            "trend_count": len(intelligence.get("trends", [])),
        },
        "signal_board": _signal_board(alerts, intelligence),
        "editor_actions": _editor_actions(health, alerts, risky_claims, intelligence),
        "claim_boundary": "控制中心聚合系统状态、风险和建议，不替代人工编辑判断。",
    }


def runtime_monitor(
    continuous_log_path: str = DEFAULT_RUN_LOG_PATH,
    async_log_path: str = DEFAULT_ASYNC_LOG_PATH,
    event_log_path: str = DEFAULT_EVENT_LOG_PATH,
) -> Dict[str, Any]:
    continuous = _read_jsonl_tail(continuous_log_path, 5)
    async_runtime = _read_jsonl_tail(async_log_path, 10)
    events = _read_jsonl_tail(event_log_path, 20)
    return {
        "continuous_runner": {
            "log_path": continuous_log_path,
            "recent_runs": continuous,
            "recent_run_count": len(continuous),
        },
        "async_runtime": {
            "log_path": async_log_path,
            "recent_events": async_runtime,
            "recent_event_count": len(async_runtime),
        },
        "events": {
            "log_path": event_log_path,
            "recent_events": events,
            "recent_event_count": len(events),
        },
    }


def _risky_claims(db_path: str) -> Dict[str, Any]:
    statuses = ["unsupported", "needs_verification", "attribution_required"]
    claims = []
    for status in statuses:
        claims.extend(claims_query(status=status, db_path=db_path, limit=20).get("claims", []))
    return {"count": len(claims), "claims": claims[:30]}


def _signal_board(alerts: Dict[str, Any], intelligence: Dict[str, Any]) -> List[Dict[str, Any]]:
    board: List[Dict[str, Any]] = []
    for warning in intelligence.get("early_warnings", []):
        board.append({"level": "warning", "source": "autonomous_intelligence", "message": warning})
    for alert in alerts.get("alerts", [])[:10]:
        board.append({"level": alert.get("level", "info"), "source": alert.get("source"), "message": alert.get("message")})
    return board or [{"level": "info", "source": "control_center", "message": "暂无强信号。"}]


def _editor_actions(
    health: Dict[str, Any],
    alerts: Dict[str, Any],
    risky_claims: Dict[str, Any],
    intelligence: Dict[str, Any],
) -> List[str]:
    actions: List[str] = []
    if health.get("overall_status") == "failed":
        actions.append("先修复健康检查 failed 项，再进入持续运行。")
    if alerts.get("alert_count", 0):
        actions.append("复盘近期 alerts，判断是否需要升级为选题会讨论。")
    if risky_claims.get("count", 0):
        actions.append("优先处理高风险 claims，补充来源或删除未核验判断。")
    for suggestion in intelligence.get("investigation_suggestions", [])[:3]:
        actions.append(f"{suggestion.get('topic')}：{suggestion.get('action')}")
    return actions or ["继续监控，暂无需要升级处理的事项。"]


def _overall_status(
    health: Dict[str, Any],
    intelligence: Dict[str, Any],
    runtime: Dict[str, Any],
    risky_claims: Dict[str, Any],
) -> str:
    if health.get("overall_status") == "failed":
        return "system_failed"
    if risky_claims.get("count", 0) >= 5:
        return "editorial_risk_high"
    if intelligence.get("early_warnings") and intelligence.get("early_warnings") != ["暂无强预警信号。"]:
        return "active_warning"
    if runtime.get("continuous_runner", {}).get("recent_run_count", 0) == 0:
        return "idle"
    return "operational"


def _read_jsonl_tail(path_text: str, limit: int) -> List[Dict[str, Any]]:
    path = Path(path_text)
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]
    rows: List[Dict[str, Any]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({"raw": line})
    return rows
