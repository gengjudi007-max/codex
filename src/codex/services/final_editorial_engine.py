from __future__ import annotations

import re
from typing import Any, Dict, List

from codex.services.deep_report_drafter import draft_deep_report
from codex.services.propaganda_detector import detect_propaganda_style
from codex.services.text_utils import normalize_text

PR_REPLACEMENTS = {
    "赋能": "提供支持",
    "深耕": "持续布局",
    "引领": "推动",
    "匠心": "品质控制",
    "美好生活": "居住和消费需求",
    "战略布局": "业务布局",
    "高质量发展": "经营质量改善",
    "全面升级": "调整升级",
    "价值共创": "协同发展",
}

RISKY_CERTAINTY = {
    "必然": "可能",
    "彻底": "一定程度上",
    "完全": "较大程度上",
    "证明": "显示出",
    "全面领先": "具有一定优势",
}


def final_edit_report(payload: Dict[str, Any], style: str = "economic_observer") -> Dict[str, Any]:
    draft = draft_deep_report(payload, style=style)
    assembled = _assemble_draft(draft)
    polished = polish_news_text(assembled, subject=payload.get("subject") or payload.get("company"))
    propaganda = detect_propaganda_style(polished)

    return {
        "mode": "final_editorial_engine",
        "style": draft["style"],
        "headline": _final_headline(draft),
        "edited_text": polished,
        "editorial_notes": _editorial_notes(draft, propaganda),
        "verification_gate": draft.get("draft_status", {}),
        "fact_check_required": draft.get("evidence_plan", {}),
        "claim_boundary": "终稿编辑引擎只做表达和结构收口；若证据、采访或来源不足，应停留在待核验稿，不进入正式终稿。",
    }


def polish_news_text(text: Any, subject: str | None = None) -> str:
    normalized = normalize_text(text)
    normalized = _replace_terms(normalized, PR_REPLACEMENTS)
    normalized = _replace_terms(normalized, RISKY_CERTAINTY)
    normalized = _third_person_view(normalized, subject)
    normalized = _normalize_company_reference(normalized, subject)
    normalized = _clean_template_phrases(normalized)
    return normalized


def _assemble_draft(draft: Dict[str, Any]) -> str:
    parts = []
    if draft.get("lead"):
        parts.append(draft["lead"].get("text", ""))
    for section in draft.get("sections", []):
        title = section.get("title", "")
        body = section.get("draft", "")
        parts.append(f"【{title}】{body}")
    if draft.get("ending"):
        parts.append(draft["ending"].get("text", ""))
    return "\n\n".join(part for part in parts if part)


def _replace_terms(text: str, replacements: Dict[str, str]) -> str:
    result = text
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result


def _third_person_view(text: str, subject: str | None) -> str:
    result = text
    replacement = subject or "该企业"
    result = re.sub(r"\b我们\b", replacement, result)
    result = result.replace("我司", replacement)
    result = result.replace("公司称", f"{replacement}称")
    return result


def _normalize_company_reference(text: str, subject: str | None) -> str:
    if not subject:
        return text
    return re.sub(r"(?<!有限)公司(?!称|表示|公告|披露)", subject, text)


def _clean_template_phrases(text: str) -> str:
    phrases = [
        "值得注意的是，",
        "不可否认的是，",
        "从某种程度上说，",
        "在这一过程中，",
    ]
    result = text
    for phrase in phrases:
        result = result.replace(phrase, "")
    return result


def _final_headline(draft: Dict[str, Any]) -> str:
    options = draft.get("headline_options") or []
    if not options:
        return "房地产调整进入深水区"
    return options[0]


def _editorial_notes(draft: Dict[str, Any], propaganda: Dict[str, Any]) -> List[str]:
    notes = [
        "已按第三方财经报道视角压缩宣传性表达。",
        "已将强确定性表达调整为审慎风险表达。",
        "正式发布前仍需逐项核验事实、数字、时间和来源。",
    ]
    status = draft.get("draft_status", {}).get("status")
    if status == "blocked_by_contradictions":
        notes.append("当前存在矛盾信息，不建议进入终稿发布。")
    if status == "outline_only_missing_sources":
        notes.append("当前缺少来源支撑，只能作为写作框架或待核验稿。")
    if propaganda.get("risk_level") != "low":
        notes.append("仍需人工复核残留宣传腔和企业口径。")
    return notes
