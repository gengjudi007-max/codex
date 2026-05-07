from __future__ import annotations

from typing import Any, Dict, List

from codex.interaction_core.pipeline import run_topic_pipeline
from codex.services.draft_editor import edit_draft
from codex.services.entity_graph import entity_profile, graph_summary
from codex.services.memory_graph import (
    build_timeline,
    link_related_events,
    memory_summary,
    remember_events,
)
from codex.services.news_rewrite_planner import plan_newsroom_rewrite
from codex.services.policy_semantics import analyze_policy_semantics
from codex.services.propaganda_detector import detect_propaganda_style
from codex.services.risk_chain import analyze_risk_chain
from codex.services.signal_monitor import monitor_signals
from codex.services.text_utils import compact_text, infer_city, infer_company, normalize_text


def run_newsroom_orchestrator(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Run an end-to-end newsroom workflow from raw input to reporting plan.

    This orchestrator intentionally stops at a verified reporting package rather than
    fabricating interviews or final facts. Draft generation can be added after claim
    extraction and fact checking are stronger.
    """
    items = _payload_to_items(payload)
    memory_path = str(payload.get("memory_path") or "data/memory_events.jsonl")

    memory_result = remember_events(items, path=memory_path)
    signal_result = monitor_signals(items)
    topic_result = run_topic_pipeline(items)
    risk_result = analyze_risk_chain({"items": items})
    policy_result = _policy_analysis(payload, items)
    memory_links = [_related_for_item(item, memory_path) for item in items]
    entity = _primary_entity(items)

    intelligence = {
        "risk_chain": risk_result,
        "policy_semantics": policy_result,
        "memory_summary": memory_summary(memory_path),
        "graph_summary": graph_summary(memory_path),
        "timeline": build_timeline(entity, memory_path) if entity else None,
        "entity_profile": entity_profile(entity, memory_path) if entity else None,
        "related_events": memory_links,
    }

    draft_text = str(payload.get("draft") or payload.get("text") or payload.get("message") or "")
    editorial = _editorial_package(draft_text) if draft_text else None

    return {
        "mode": "newsroom_orchestrator",
        "input_count": len(items),
        "memory": memory_result,
        "signals": signal_result,
        "topics": topic_result,
        "intelligence": intelligence,
        "reporting_package": _build_reporting_package(topic_result, risk_result, policy_result),
        "editorial": editorial,
        "next_actions": _next_actions(topic_result, risk_result, policy_result),
        "claim_boundary": "总流程只生成选题、分析、采访和核验方案；未经材料和采访证实，不自动生成最终事实结论。",
    }


def _payload_to_items(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    if isinstance(payload.get("items"), list):
        return [_normalize_item(item) for item in payload["items"] if isinstance(item, dict)]

    text = str(payload.get("text") or payload.get("message") or payload.get("content") or "")
    if not text.strip():
        return []
    return [
        _normalize_item(
            {
                "source": payload.get("source") or "user",
                "title": payload.get("title") or compact_text(text, 80),
                "summary": text,
                "content": text,
            }
        )
    ]


def _normalize_item(item: Dict[str, Any]) -> Dict[str, Any]:
    text = normalize_text(" ".join(str(item.get(key, "")) for key in ("title", "summary", "content", "text", "message")))
    normalized = dict(item)
    normalized.setdefault("title", compact_text(text, 80) or "未命名信息")
    normalized.setdefault("summary", compact_text(text, 240))
    normalized.setdefault("source", "unknown")
    normalized.setdefault("city", infer_city(text))
    normalized.setdefault("company", infer_company(text))
    return normalized


def _policy_analysis(payload: Dict[str, Any], items: List[Dict[str, Any]]) -> Dict[str, Any]:
    current = payload.get("current_policy") or payload.get("current") or _items_text(items)
    previous = payload.get("previous_policy") or payload.get("previous") or ""
    return analyze_policy_semantics(current, previous)


def _related_for_item(item: Dict[str, Any], memory_path: str) -> Dict[str, Any]:
    related = link_related_events(item, path=memory_path, limit=5)
    return {
        "title": item.get("title"),
        "related_count": related.get("related_count", 0),
        "related_events": related.get("related_events", []),
    }


def _primary_entity(items: List[Dict[str, Any]]) -> str:
    for item in items:
        if item.get("city"):
            return str(item["city"])
        if item.get("company"):
            return str(item["company"])
    return ""


def _editorial_package(text: str) -> Dict[str, Any]:
    return {
        "draft_check": edit_draft(text),
        "propaganda_check": detect_propaganda_style(text),
        "rewrite_plan": plan_newsroom_rewrite(text),
    }


def _build_reporting_package(
    topic_result: Dict[str, Any],
    risk_result: Dict[str, Any],
    policy_result: Dict[str, Any],
) -> Dict[str, Any]:
    topics = topic_result.get("topics", [])
    top_topic = topics[0] if topics else {}
    return {
        "lead_topic": top_topic.get("topic"),
        "angle": top_topic.get("angle"),
        "priority": top_topic.get("priority"),
        "material_plan": top_topic.get("material_plan"),
        "interview_plan": top_topic.get("interview_plan"),
        "photo_plan": top_topic.get("photo_plan"),
        "risk_nodes": risk_result.get("risk_map", {}).get("nodes", []),
        "policy_focus": policy_result.get("policy_focus", {}),
        "verification_status": top_topic.get("verification_status"),
        "limitations": top_topic.get("limitations", []),
    }


def _next_actions(
    topic_result: Dict[str, Any],
    risk_result: Dict[str, Any],
    policy_result: Dict[str, Any],
) -> List[str]:
    actions = [
        "核验所有核心数字、公告、政策原文和统计口径。",
        "将企业说法、研究机构判断和记者分析分开标注。",
    ]
    if topic_result.get("topics"):
        actions.append("优先推进评分最高选题的采访对象预约和材料补齐。")
    if risk_result.get("chains"):
        actions.append("沿风险链继续追踪资金来源、项目状态和主体责任。")
    if policy_result.get("semantic_shifts"):
        actions.append("对比前后政策原文，确认措辞变化是否具有实质政策含义。")
    return actions


def _items_text(items: List[Dict[str, Any]]) -> str:
    return normalize_text(" ".join(str(item.get(key, "")) for item in items for key in ("title", "summary", "content")))
