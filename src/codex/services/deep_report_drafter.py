from __future__ import annotations

from typing import Any, Dict, List

from codex.services.story_architecture import build_story_architecture
from codex.services.text_utils import compact_text, normalize_text


def draft_deep_report(
    payload: Dict[str, Any],
    style: str = "economic_observer",
    target_length: str = "outline",
) -> Dict[str, Any]:
    """Draft a guarded deep-report package based on story architecture.

    This function creates a newsroom-ready draft scaffold. It does not invent
    interviews, undisclosed data, or unverifiable conclusions.
    """
    architecture = build_story_architecture(payload, style=style)
    lead = _draft_lead(payload, architecture)
    sections = _draft_sections(architecture)
    ending = _draft_ending(architecture)

    return {
        "mode": "deep_report_draft",
        "style": architecture["style"],
        "target_length": target_length,
        "headline_options": architecture["headline_options"],
        "lead": lead,
        "sections": sections,
        "ending": ending,
        "evidence_plan": architecture["evidence_plan"],
        "interview_slots": architecture["interview_slots"],
        "risk_and_balance": architecture["risk_and_balance"],
        "do_not_write": architecture["do_not_write"],
        "draft_status": _draft_status(architecture),
        "claim_boundary": "该模块生成的是带核验标记的深度报道初稿框架，不生成未经证实的采访、数据和结论。",
    }


def _draft_lead(payload: Dict[str, Any], architecture: Dict[str, Any]) -> Dict[str, str]:
    source_text = _source_text(payload)
    lead_type = architecture["lead_options"][0]["type"] if architecture.get("lead_options") else "事件切入"
    style_name = architecture["style"]["name"]
    base = compact_text(source_text, 180) if source_text else "【待补新闻由头】"
    if style_name == "财新":
        text = (
            f"{base}。这一变化的核心不只在事件本身，更在于其背后的数据口径、资金来源、"
            "政策约束和风险传导仍需逐项核验。"
        )
    else:
        text = (
            f"{base}。在房地产行业进入存量调整周期后，类似变化已不再只是单个主体的动作，"
            "而是折射出市场、资金与政策之间重新平衡的过程。"
        )
    return {"type": lead_type, "text": text, "verification_note": "导语中的事实需对应原始材料或采访记录。"}


def _draft_sections(architecture: Dict[str, Any]) -> List[Dict[str, Any]]:
    sections = []
    for plan in architecture.get("section_plan", []):
        title = plan.get("title") or "小标题"
        sections.append(
            {
                "title": title,
                "draft": _section_paragraph(title, plan, architecture),
                "evidence_needed": plan.get("evidence_needed") or plan.get("risk_nodes") or plan.get("open_questions") or [],
                "interview_needed": _matching_interviews(title, architecture.get("interview_slots", [])),
                "editor_notes": plan.get("writing_notes", []),
            }
        )
    return sections


def _section_paragraph(title: str, plan: Dict[str, Any], architecture: Dict[str, Any]) -> str:
    style_name = architecture["style"]["name"]
    purpose = plan.get("purpose", "")
    if "事实" in title:
        return (
            f"这一部分应围绕“{purpose}”展开。写作时先交代已经可以核验的事实，"
            "包括时间、主体、动作、数据和来源；对于企业说法，应明确归属，不能直接写成媒体判断。"
            "【待补：原始公告/财报/政策文件/采访记录】"
        )
    if "为什么" in title:
        tone = "用证据链解释因果关系" if style_name == "财新" else "把事件放入行业周期中解释"
        return (
            f"这一部分重点是{tone}。可从政策变化、市场下行、资金约束、土地财政或企业财务压力切入，"
            "但所有因果判断都应保留边界。若证据不足，应写为“可能相关”“仍待观察”，而不是确定结论。"
            "【待补：第三方分析、可比数据、反向信息】"
        )
    return (
        f"这一部分应回答“{purpose}”。结尾不宜写成企业愿景，而应回到行业层面，"
        "说明该事件对企业、城市、投资者、购房者或业主可能产生的影响，并列出后续观察指标。"
        "【待补：后续跟踪清单和关键采访】"
    )


def _draft_ending(architecture: Dict[str, Any]) -> Dict[str, str]:
    risk_nodes = architecture.get("risk_and_balance", {}).get("risk_nodes", [])
    risk_text = "、".join(risk_nodes[:4]) if risk_nodes else "行业调整"
    return {
        "text": (
            f"从更长周期看，{risk_text}并非孤立现象。对房地产财经报道而言，真正需要继续追踪的，"
            "是这些变化是否会在财务报表、土地市场、项目交付、地方财政和居民端形成持续反馈。"
            "在证据链尚未闭合前，相关判断仍应保持克制。"
        ),
        "verification_note": "结尾只做基于已识别风险的审慎归纳，不替代事实核查。",
    }


def _matching_interviews(title: str, slots: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if "事实" in title:
        return [slot for slot in slots if "企业" in slot.get("role", "") or "数据" in slot.get("purpose", "")]
    if "为什么" in title:
        return [slot for slot in slots if "政策" in slot.get("role", "") or "第三方" in slot.get("role", "")]
    return slots


def _draft_status(architecture: Dict[str, Any]) -> Dict[str, Any]:
    evidence = architecture.get("evidence_plan", {})
    contradictions = evidence.get("contradiction_count", 0)
    source_count = evidence.get("source_count", 0)
    if contradictions:
        status = "blocked_by_contradictions"
    elif source_count == 0:
        status = "outline_only_missing_sources"
    else:
        status = "draftable_with_verification"
    return {
        "status": status,
        "source_count": source_count,
        "contradiction_count": contradictions,
        "required_before_final": [
            "补齐一手来源或权威来源。",
            "核验所有数字、时间和主体。",
            "补充至少一个非企业口径信源。",
            "清理宣传性、绝对化和强因果表达。",
        ],
    }


def _source_text(payload: Dict[str, Any]) -> str:
    if payload.get("text") or payload.get("message") or payload.get("content"):
        return normalize_text(payload.get("text") or payload.get("message") or payload.get("content"))
    if isinstance(payload.get("items"), list):
        return normalize_text(" ".join(str(item.get("summary") or item.get("title") or "") for item in payload["items"] if isinstance(item, dict)))
    return ""
