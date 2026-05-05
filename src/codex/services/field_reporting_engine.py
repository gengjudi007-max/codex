from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


FIELD_TYPES = [
    "sales_quote",
    "buyer_quote",
    "broker_quote",
    "project_scene",
    "site_observation",
    "marketing_action",
    "price_action",
    "customer_behavior",
]


@dataclass
class FieldMaterial:
    """现场材料。

    source_level:
        1 = 记者自采/录音/现场笔记
        2 = 企业或项目方直接回应
        3 = 权威机构调研材料
        4 = 媒体公开探访，仅可辅助使用
    """

    material_type: str
    city: str
    project: Optional[str]
    speaker: Optional[str]
    content: str
    source: str
    source_level: int = 1
    verified: bool = False
    topic_tags: Optional[List[str]] = None


def enhance_with_field_reporting(
    article_sections: List[Dict[str, Any]],
    field_materials: List[Dict[str, Any]],
    topic: str,
) -> Dict[str, Any]:
    """为深度报道稿件增强现场表达。

    规则：
    1. 不自动编造现场、采访或项目成交情况；
    2. 只使用与主题直接相关的现场材料；
    3. 低可信材料只能作为现场观察，不作为核心事实依据；
    4. 对缺少现场材料的部分生成补采清单。
    """
    normalized_materials = [_normalize_material(item) for item in field_materials]
    relevant_materials = [
        item for item in normalized_materials if _is_relevant_to_topic(item, topic)
    ]

    enhanced_sections = []
    gaps = []

    for section in article_sections:
        matched = _match_materials_for_section(section, relevant_materials)
        if matched:
            enhanced_sections.append(_inject_field_material(section, matched))
        else:
            enhanced_sections.append(section)
            gaps.append(_build_gap(section, topic))

    return {
        "sections": enhanced_sections,
        "used_materials": [_material_to_dict(item) for item in relevant_materials],
        "field_gaps": gaps,
        "follow_up_interview_plan": build_follow_up_interview_plan(gaps, topic),
        "rules": FIELD_REPORTING_RULES,
    }


def build_follow_up_interview_plan(gaps: List[Dict[str, Any]], topic: str) -> List[Dict[str, Any]]:
    """根据现场材料缺口生成补采计划。"""
    plan = []
    for gap in gaps:
        section_title = gap.get("section_title", "未命名部分")
        plan.append(
            {
                "section": section_title,
                "target_materials": gap.get("missing_materials", []),
                "interview_targets": _suggest_targets(topic, section_title),
                "questions": _suggest_questions(topic, section_title),
            }
        )
    return plan


FIELD_REPORTING_RULES = {
    "do_not_fabricate": "不得编造销售人员、客户、项目成交和现场细节。",
    "topic_relevance": "现场材料必须直接服务主选题，不得为了丰富稿件硬塞无关案例。",
    "source_hierarchy": "记者自采和项目直接回应优先，公开探访材料只能辅助。",
    "quote_handling": "未经核实的原话不加引号，可改为概述性表述，如‘一位项目销售人员称’。",
    "risk_control": "涉及企业、项目、价格、成交时，尽量使用‘部分、个别、该项目、该区域’等范围限定。",
}


def _normalize_material(item: Dict[str, Any]) -> FieldMaterial:
    return FieldMaterial(
        material_type=item.get("material_type", "site_observation"),
        city=item.get("city", ""),
        project=item.get("project"),
        speaker=item.get("speaker"),
        content=item.get("content", ""),
        source=item.get("source", "unknown"),
        source_level=int(item.get("source_level", 4)),
        verified=bool(item.get("verified", False)),
        topic_tags=item.get("topic_tags", []),
    )


def _is_relevant_to_topic(material: FieldMaterial, topic: str) -> bool:
    text = " ".join(
        [
            material.material_type,
            material.city,
            material.project or "",
            material.content,
            " ".join(material.topic_tags or []),
        ]
    )
    topic_keywords = _topic_keywords(topic)
    return any(keyword in text for keyword in topic_keywords)


def _topic_keywords(topic: str) -> List[str]:
    if "五一" in topic or "假期" in topic or "成交" in topic:
        return ["五一", "假期", "来访", "认购", "成交", "去化", "看房", "优惠", "折扣"]
    if "城投" in topic or "拿地" in topic or "土地" in topic:
        return ["城投", "拿地", "土拍", "底价", "溢价", "流拍", "专项债", "收储"]
    if "年报" in topic or "利润" in topic or "房企" in topic:
        return ["年报", "利润", "减值", "现金流", "融资", "销售额", "业绩"]
    return [word for word in topic.split() if word]


def _match_materials_for_section(
    section: Dict[str, Any], materials: List[FieldMaterial]
) -> List[FieldMaterial]:
    title = section.get("title", "")
    body = section.get("content", "")
    section_text = f"{title} {body}"

    scored = []
    for material in materials:
        score = 0
        if material.city and material.city in section_text:
            score += 3
        if material.project and material.project in section_text:
            score += 4
        for tag in material.topic_tags or []:
            if tag in section_text:
                score += 2
        if material.material_type in ["sales_quote", "buyer_quote", "project_scene"]:
            score += 1
        if material.verified:
            score += 1
        if score > 0:
            scored.append((score, material))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in scored[:3]]


def _inject_field_material(
    section: Dict[str, Any], materials: List[FieldMaterial]
) -> Dict[str, Any]:
    paragraphs = [section.get("content", "").strip()]
    for material in materials:
        paragraphs.append(_render_material(material))

    enhanced = dict(section)
    enhanced["content"] = "\n\n".join(p for p in paragraphs if p)
    enhanced["field_material_count"] = len(materials)
    return enhanced


def _render_material(material: FieldMaterial) -> str:
    prefix_parts = []
    if material.city:
        prefix_parts.append(material.city)
    if material.project:
        prefix_parts.append(material.project)

    place = "".join(prefix_parts)

    if material.material_type == "sales_quote":
        speaker = material.speaker or "项目销售人员"
        return f"{place}一位{speaker}称，{material.content}"
    if material.material_type == "buyer_quote":
        speaker = material.speaker or "购房者"
        return f"{place}一位{speaker}表示，{material.content}"
    if material.material_type == "broker_quote":
        speaker = material.speaker or "经纪人"
        return f"{place}一位{speaker}称，{material.content}"
    if material.material_type == "project_scene":
        return f"在{place}，现场情况显示，{material.content}"
    if material.material_type == "marketing_action":
        return f"{place}在假期前后调整了营销安排，{material.content}"
    if material.material_type == "price_action":
        return f"{place}价格端也有变化，{material.content}"
    if material.material_type == "customer_behavior":
        return f"{place}客户行为出现变化，{material.content}"
    return f"{place}现场材料显示，{material.content}"


def _build_gap(section: Dict[str, Any], topic: str) -> Dict[str, Any]:
    title = section.get("title", "未命名部分")
    missing = []
    if "成交" in title or "回暖" in title or "假期" in topic:
        missing.extend(["项目来访变化", "认购/成交变化", "销售人员说法", "客户到访行为"])
    if "客户" in title or "需求" in title:
        missing.extend(["购房者采访", "经纪人观察", "置换链条案例"])
    if "价格" in title or "预期" in title:
        missing.extend(["折扣变化", "价格口径", "客户议价行为"])
    if not missing:
        missing.extend(["现场观察", "一线采访", "项目样本"])
    return {"section_title": title, "missing_materials": list(dict.fromkeys(missing))}


def _suggest_targets(topic: str, section_title: str) -> List[str]:
    targets = ["项目销售人员", "购房者", "中介经纪人"]
    if "政策" in topic or "政策" in section_title:
        targets.append("机构分析师")
    if "价格" in section_title:
        targets.append("房企营销负责人")
    return targets


def _suggest_questions(topic: str, section_title: str) -> List[str]:
    return [
        "假期期间来访量和认购量较节前是否有变化？",
        "成交主要集中在哪类户型、总价段和楼层？",
        "项目是否推出折扣、特价房或渠道政策？",
        "客户决策周期较此前是否缩短或延长？",
        "成交客户以刚需、改善还是置换为主？",
    ]


def _material_to_dict(material: FieldMaterial) -> Dict[str, Any]:
    return {
        "material_type": material.material_type,
        "city": material.city,
        "project": material.project,
        "speaker": material.speaker,
        "content": material.content,
        "source": material.source,
        "source_level": material.source_level,
        "verified": material.verified,
        "topic_tags": material.topic_tags or [],
    }
