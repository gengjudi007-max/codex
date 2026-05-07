from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from codex.services.continuous_runner import run_once
from codex.services.deep_report_drafter import draft_deep_report
from codex.services.fact_check_engine import run_fact_check
from codex.services.final_editorial_engine import final_edit_report
from codex.services.real_estate_reasoning import reason_real_estate
from codex.services.story_architecture import build_story_architecture


def run_newsroom_desk(config_path: str = "config/watchlist.json") -> Dict[str, Any]:
    """Run one editorial-desk cycle: monitor, judge, assign, draft, and gate."""
    run_result = run_once(config_path)
    items = _items_from_run(run_result)
    morning_brief = build_morning_brief(run_result)
    topic_pool = build_topic_pool(run_result)
    assignments = build_assignments(topic_pool)
    publication_gates = [_publication_gate(item) for item in items[:5]]

    return {
        "mode": "newsroom_desk",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "morning_brief": morning_brief,
        "topic_pool": topic_pool,
        "assignments": assignments,
        "publication_gates": publication_gates,
        "desk_status": _desk_status(run_result, topic_pool, publication_gates),
        "next_editor_actions": _next_editor_actions(topic_pool, publication_gates),
        "claim_boundary": "编辑部模式提供选题、派单和发稿门建议，不替代记者采访、编辑终审和法律审核。",
    }


def build_morning_brief(run_result: Dict[str, Any]) -> Dict[str, Any]:
    ingestion = run_result.get("ingestion", {})
    orchestrator = run_result.get("orchestrator") or {}
    alerts = run_result.get("alerts", [])
    return {
        "headline": _brief_headline(alerts, orchestrator),
        "source_status": {
            "accepted_count": ingestion.get("accepted_count", 0),
            "error_count": ingestion.get("error_count", 0),
            "source_types": ingestion.get("source_types", []),
        },
        "lead_topic": orchestrator.get("lead_topic"),
        "risk_nodes": orchestrator.get("risk_nodes", []),
        "alerts": alerts,
    }


def build_topic_pool(run_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    orchestrator = run_result.get("orchestrator") or {}
    lead_topic = orchestrator.get("lead_topic")
    risk_nodes = orchestrator.get("risk_nodes", [])
    if not lead_topic:
        return []
    priority_score = 60 + min(len(risk_nodes) * 5, 30)
    return [
        {
            "topic": lead_topic,
            "priority": "high" if priority_score >= 80 else "medium",
            "priority_score": priority_score,
            "risk_nodes": risk_nodes,
            "recommended_format": "深度报道" if priority_score >= 80 else "行业观察",
            "desk_reason": "由持续监控流程识别，已出现风险链或选题信号。",
        }
    ]


def build_assignments(topic_pool: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    assignments = []
    for topic in topic_pool:
        assignments.append(
            {
                "topic": topic["topic"],
                "owner_role": "房地产财经记者",
                "editor_role": "深度报道编辑",
                "deadline": "下一次编辑会前形成采访和材料清单",
                "must_do": [
                    "补齐一手来源或权威来源。",
                    "确认核心数字口径。",
                    "至少采访一个非企业口径信源。",
                    "形成风险链和反向论证。",
                ],
            }
        )
    return assignments


def _publication_gate(item: Dict[str, Any]) -> Dict[str, Any]:
    text = item.get("content") or item.get("summary") or item.get("title") or ""
    fact_check = run_fact_check(text, sources=[])
    reasoning = reason_real_estate({"text": text})
    story = build_story_architecture({"text": text})
    draft = draft_deep_report({"text": text})
    final = final_edit_report({"text": text})
    return {
        "title": item.get("title"),
        "fact_check_status": fact_check.get("verification", {}).get("overall_status"),
        "reasoning_chains": [chain.get("name") for chain in reasoning.get("causal_chains", [])],
        "story_sections": [section.get("title") for section in story.get("section_plan", [])],
        "draft_status": draft.get("draft_status", {}).get("status"),
        "final_gate_notes": final.get("editorial_notes", []),
        "can_publish": _can_publish(fact_check, draft),
    }


def _items_from_run(run_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    # continuous_runner intentionally compacts output. The desk therefore uses
    # the available brief data and leaves detailed item retrieval to source_store.
    orchestrator = run_result.get("orchestrator") or {}
    lead_topic = orchestrator.get("lead_topic")
    if not lead_topic:
        return []
    return [
        {
            "title": lead_topic,
            "summary": "；".join(orchestrator.get("risk_nodes", [])) or lead_topic,
            "source": "continuous_runner",
        }
    ]


def _can_publish(fact_check: Dict[str, Any], draft: Dict[str, Any]) -> bool:
    return (
        fact_check.get("verification", {}).get("overall_status") == "verified_with_sources"
        and draft.get("draft_status", {}).get("status") == "draftable_with_verification"
    )


def _desk_status(
    run_result: Dict[str, Any],
    topic_pool: List[Dict[str, Any]],
    publication_gates: List[Dict[str, Any]],
) -> str:
    if run_result.get("ingestion", {}).get("error_count", 0):
        return "needs_source_maintenance"
    if any(not gate.get("can_publish") for gate in publication_gates):
        return "reporting_required_before_publish"
    if topic_pool:
        return "active_topics_ready_for_assignment"
    return "quiet"


def _next_editor_actions(topic_pool: List[Dict[str, Any]], publication_gates: List[Dict[str, Any]]) -> List[str]:
    actions = []
    if topic_pool:
        actions.append("召开小型选题会，确认最高优先级选题是否进入深稿流程。")
    if publication_gates:
        actions.append("逐项核验发稿门中未通过的事实、来源和矛盾问题。")
    if not actions:
        actions.append("继续监控数据源，暂不启动深稿。")
    return actions


def _brief_headline(alerts: List[str], orchestrator: Dict[str, Any]) -> str:
    if orchestrator.get("lead_topic"):
        return f"今日重点：{orchestrator['lead_topic']}"
    if alerts:
        return alerts[0]
    return "今日暂无强信号"
