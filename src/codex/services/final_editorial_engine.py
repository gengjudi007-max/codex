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
    if payload.get("sources"):
        from codex.services.grounded_report import write_grounded_report
        report = write_grounded_report(payload)
        return {**report, "mode": "final_editorial_engine", "style": style,
                "edited_text": report["article_text"],
                "editorial_notes": report["verification_gate"]["issues"],
                "fact_check_required": report["paragraphs"]}
    # Editing an existing draft must not append an unrelated writing scaffold.
    text = payload.get("draft") or payload.get("text") or payload.get("message") or ""
    polished = polish_news_text(text, subject=payload.get("subject") or payload.get("company"))
    return {"mode": "final_editorial_engine", "style": style,
            "headline": str(payload.get("headline") or ""), "edited_text": polished,
            "editorial_notes": ["原稿精校；未提供来源正文，事实仍需核验。"],
            "verification_gate": {"status": "unverified_draft" if polished else "blocked_missing_source_content", "publishable": False},
            "fact_check_required": [], "claim_boundary": "不自动确认事实或发布稿件。"}


def polish_news_text(text: Any, subject: str | None = None) -> str:
    # Preserve quotations and paragraph structure. Certainty and promotional
    # claims require an editorial decision, not synonym substitution.
    original = str(text or "").strip()
    parts = re.split(r'(“[^”]*”|「[^」]*」|‘[^’]*’|"[^"\n]*")', original)
    for index in range(0, len(parts), 2):
        segment = parts[index]
        if subject:
            # Resolve only standalone sentence-initial references; never alter
            # registered names, subsidiaries, or references to other companies.
            segment = re.sub(
                r"(^|[。！？\n])([ \t]*)(?:我们|我司|公司)(?=将|始终|持续|坚持|致力于|称|表示|披露)",
                lambda match: match.group(1) + match.group(2) + str(subject),
                segment,
            )
        segment = re.sub(r"(^|[。！？\n])([ \t]*)(?:值得注意的是|不可否认的是|从某种程度上说|在这一过程中)，", r"\1\2", segment)
        parts[index] = segment
    return "".join(parts)


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
        "仅清理句首套话；有明确主体时调整独立的企业自称，保留引语和专名。",
        "宣传性、绝对化和因果判断需人工核验，不以近义词替换改变原意。",
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
