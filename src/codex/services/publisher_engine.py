from __future__ import annotations

from typing import Any, Dict, List, Optional

from codex.services.final_check_engine import run_final_check
from codex.services.field_reporting_engine import enhance_with_field_reporting
from codex.services.interview_material_store import render_interview_material


BANNED_AI_PATTERNS = [
    "整体来看",
    "从数据来看",
    "可以看出",
    "本质上",
    "意味着",
    "值得注意的是",
    "需要指出的是",
    "进一步来看",
    "可以发现",
]


NEUTRAL_REPLACEMENTS = {
    "整体来看，": "",
    "从数据来看，": "",
    "可以看出，": "",
    "本质上，": "",
    "这意味着": "相关变化显示",
    "值得注意的是，": "",
    "需要指出的是，": "",
    "进一步来看，": "",
    "可以发现，": "",
}


def generate_publish_ready_article(
    topic: str,
    article: Dict[str, Any],
    sources: List[Dict[str, Any]],
    interview_materials: Optional[List[Dict[str, Any]]] = None,
    field_materials: Optional[List[Dict[str, Any]]] = None,
    max_fix_rounds: int = 2,
) -> Dict[str, Any]:
    """最终成稿引擎。

    输出三类版本：
    1. publish_version：可交稿版本，尽量只保留已核验内容；
    2. editor_version：编辑审阅版本，附带问题清单；
    3. repair_plan：如未通过终检，列出需补数据、补采访、删改风险表达的位置。

    设计原则：
    - 不编造数据；
    - 不编造采访；
    - 不强行使用低相关案例；
    - 未核验内容进入问题清单，而不是直接进入终稿；
    - 默认采用客观、事实陈述型财经报道表达。
    """
    interview_materials = interview_materials or []
    field_materials = field_materials or []

    working_article = _normalize_article(article)
    working_article = _inject_interview_materials(working_article, interview_materials, topic)
    working_article = _inject_field_materials(working_article, field_materials, topic)
    working_article = _neutralize_article(working_article)

    check_report = run_final_check(
        article=working_article,
        sources=sources,
        interview_materials=interview_materials,
        topic=topic,
    )

    rounds = 0
    while not check_report.get("pass_status") and rounds < max_fix_rounds:
        working_article = _auto_repair_article(working_article, check_report)
        check_report = run_final_check(
            article=working_article,
            sources=sources,
            interview_materials=interview_materials,
            topic=topic,
        )
        rounds += 1

    return {
        "publish_version": render_article(working_article),
        "editor_version": {
            "article": working_article,
            "final_check": check_report,
        },
        "repair_plan": build_repair_plan(check_report),
        "pass_status": check_report.get("pass_status"),
        "score": check_report.get("score"),
    }


def render_article(article: Dict[str, Any]) -> str:
    """按正式成稿格式输出，不显示“标题/导语”等标签。"""
    parts = []
    title = article.get("title", "").strip()
    lead = article.get("lead", "").strip()
    if title:
        parts.append(title)
    if lead:
        parts.append(lead)
    for section in article.get("sections", []):
        section_title = section.get("title", "").strip()
        content = section.get("content", "").strip()
        if section_title:
            parts.append(section_title)
        if content:
            parts.append(content)
    return "\n\n".join(parts)


def build_repair_plan(check_report: Dict[str, Any]) -> Dict[str, Any]:
    """根据终检结果生成补修计划。"""
    data_gaps = []
    interview_gaps = []
    legal_risks = []
    style_notes = []
    topic_issues = []

    for issue in check_report.get("issues", []):
        category = issue.get("category")
        item = {
            "location": issue.get("location"),
            "message": issue.get("message"),
            "suggestion": issue.get("suggestion"),
        }
        if category in ["fact_source", "source", "source_whitelist", "source_verification"]:
            data_gaps.append(item)
        elif category in ["interview_material", "direct_quote", "interview_fact"]:
            interview_gaps.append(item)
        elif category == "legal_risk_expression":
            legal_risks.append(item)
        elif category == "style_ai_pattern":
            style_notes.append(item)
        elif category == "topic_relevance":
            topic_issues.append(item)

    return {
        "data_gaps": data_gaps,
        "interview_gaps": interview_gaps,
        "legal_risks": legal_risks,
        "style_notes": style_notes,
        "topic_issues": topic_issues,
        "next_actions": _next_actions(data_gaps, interview_gaps, legal_risks, topic_issues),
    }


def _normalize_article(article: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "title": article.get("title", "").strip(),
        "lead": article.get("lead", "").strip(),
        "sections": [
            {
                "title": section.get("title", "").strip(),
                "content": section.get("content", "").strip(),
            }
            for section in article.get("sections", [])
        ],
    }


def _inject_interview_materials(
    article: Dict[str, Any],
    materials: List[Dict[str, Any]],
    topic: str,
) -> Dict[str, Any]:
    usable = [
        item
        for item in materials
        if item.get("status") in ["checked", "usable", "background_only"]
        and item.get("status") != "do_not_use"
        and _is_material_relevant(item, topic)
    ]
    if not usable:
        return article

    sections = []
    for section in article.get("sections", []):
        matched = _match_materials(section, usable)
        content = section.get("content", "")
        additions = []
        for material in matched[:2]:
            if material.get("status") == "background_only":
                continue
            additions.append(render_interview_material(material))
        if additions:
            content = content + "\n\n" + "\n\n".join(additions)
        sections.append({"title": section.get("title", ""), "content": content})
    article["sections"] = sections
    return article


def _inject_field_materials(
    article: Dict[str, Any],
    materials: List[Dict[str, Any]],
    topic: str,
) -> Dict[str, Any]:
    if not materials:
        return article
    enhanced = enhance_with_field_reporting(article.get("sections", []), materials, topic)
    article["sections"] = enhanced.get("sections", article.get("sections", []))
    article["field_gaps"] = enhanced.get("field_gaps", [])
    article["follow_up_interview_plan"] = enhanced.get("follow_up_interview_plan", [])
    return article


def _neutralize_article(article: Dict[str, Any]) -> Dict[str, Any]:
    article["title"] = _neutralize_text(article.get("title", ""))
    article["lead"] = _neutralize_text(article.get("lead", ""))
    sections = []
    for section in article.get("sections", []):
        sections.append(
            {
                "title": _neutralize_text(section.get("title", "")),
                "content": _neutralize_text(section.get("content", "")),
            }
        )
    article["sections"] = sections
    return article


def _neutralize_text(text: str) -> str:
    cleaned = text
    for pattern, replacement in NEUTRAL_REPLACEMENTS.items():
        cleaned = cleaned.replace(pattern, replacement)
    for pattern in BANNED_AI_PATTERNS:
        cleaned = cleaned.replace(pattern, "")
    return _tidy_text(cleaned)


def _auto_repair_article(article: Dict[str, Any], check_report: Dict[str, Any]) -> Dict[str, Any]:
    """自动修复可安全处理的问题。

    只处理：
    - AI模板句；
    - 高风险绝对化表达；
    - 明显重复空白。

    不自动补数据，不自动补采访。
    """
    risk_replacements = {
        "全面复苏": "部分城市成交活跃度提升",
        "必然": "可能",
        "一定": "可能",
        "彻底": "明显",
        "暴雷": "出现债务压力",
        "崩盘": "成交明显下降",
        "造假": "真实性有待核验",
        "违规": "合规情况有待核验",
        "内幕": "相关情况",
        "资金链断裂": "流动性压力加大",
    }

    def repair_text(text: str) -> str:
        repaired = _neutralize_text(text)
        for old, new in risk_replacements.items():
            repaired = repaired.replace(old, new)
        return _tidy_text(repaired)

    article["title"] = repair_text(article.get("title", ""))
    article["lead"] = repair_text(article.get("lead", ""))
    article["sections"] = [
        {
            "title": repair_text(section.get("title", "")),
            "content": repair_text(section.get("content", "")),
        }
        for section in article.get("sections", [])
    ]
    return article


def _match_materials(section: Dict[str, Any], materials: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    text = f"{section.get('title', '')} {section.get('content', '')}"
    scored = []
    for material in materials:
        score = 0
        for tag in material.get("topic_tags", []) or []:
            if tag in text:
                score += 2
        for field in ["city", "project", "company"]:
            value = material.get(field)
            if value and value in text:
                score += 3
        if material.get("role") in ["developer_sales", "broker", "buyer"]:
            score += 1
        if score > 0:
            scored.append((score, material))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in scored]


def _is_material_relevant(material: Dict[str, Any], topic: str) -> bool:
    text = " ".join(
        [
            topic,
            " ".join(material.get("topic_tags", []) or []),
            material.get("content", ""),
            material.get("city", "") or "",
            material.get("project", "") or "",
            material.get("company", "") or "",
        ]
    )
    if "五一" in topic:
        return any(k in text for k in ["五一", "成交", "来访", "认购", "看房", "优惠", "折扣"])
    if "土地" in topic or "城投" in topic:
        return any(k in text for k in ["土地", "城投", "拿地", "土拍", "底价", "溢价"])
    if "年报" in topic or "利润" in topic:
        return any(k in text for k in ["年报", "利润", "营收", "减值", "现金流"])
    return True


def _next_actions(
    data_gaps: List[Dict[str, Any]],
    interview_gaps: List[Dict[str, Any]],
    legal_risks: List[Dict[str, Any]],
    topic_issues: List[Dict[str, Any]],
) -> List[str]:
    actions = []
    if data_gaps:
        actions.append("补充或替换数据来源，优先使用政府官网、交易所、中指、CRIC、Wind等白名单来源。")
    if interview_gaps:
        actions.append("补充采访授权、核验依据，或将直接引语改为背景表述。")
    if legal_risks:
        actions.append("删除或改写高风险定性表达，改用事实陈述。")
    if topic_issues:
        actions.append("检查低相关段落，删除不能直接服务主选题的案例和分析。")
    if not actions:
        actions.append("可进入编辑审阅或发布流程。")
    return actions


def _tidy_text(text: str) -> str:
    cleaned = text.replace("  ", " ").replace("。。", "。")
    cleaned = cleaned.replace("，，", "，").replace("\n\n\n", "\n\n")
    return cleaned.strip()
