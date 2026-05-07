from __future__ import annotations

from typing import Any, Dict, List

from codex.services.evidence import attach_credibility
from codex.services.interview_planner import plan_interview
from codex.services.material_builder import build_materials
from codex.services.photo_planner import plan_photography
from codex.services.text_utils import compact_text, infer_city, infer_company
from codex.services.topic_finder import find_topics
from codex.services.topic_scoring import score_topics


def run_topic_pipeline(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    normalized_items = [_normalize_item(item) for item in items if isinstance(item, dict)]
    topics = score_topics(find_topics({"items": normalized_items}))
    enriched_topics = []

    for topic in topics:
        material_plan = build_materials(topic)
        interview_plan = plan_interview(topic)
        photo_plan = plan_photography(topic)
        source_item = topic.get("input_item") if isinstance(topic.get("input_item"), dict) else topic
        enriched = attach_credibility(
            {key: value for key, value in topic.items() if key != "input_item"},
            source_item,
            required_materials=material_plan.get("must_have", []),
        )
        enriched["material_plan"] = material_plan
        enriched["interview_plan"] = interview_plan
        enriched["photo_plan"] = photo_plan
        enriched_topics.append(enriched)

    return {
        "input_count": len(normalized_items),
        "topic_count": len(enriched_topics),
        "topics": enriched_topics,
        "warnings": _pipeline_warnings(items, normalized_items, enriched_topics),
        "message": _build_topic_message(enriched_topics),
    }


def message_to_item(message: str) -> Dict[str, Any]:
    return {
        "source": "user",
        "title": compact_text(message, 60) or "用户输入",
        "summary": message,
        "content": message,
        "city": infer_city(message),
        "company": infer_company(message),
    }


def _build_topic_message(topics: List[Dict[str, Any]]) -> str:
    if not topics:
        return "暂未匹配到明确选题。可以补充政策措辞、公司公告、土地成交或金融工具等关键词。"

    top = topics[0]
    return f"已识别 {len(topics)} 个选题，优先处理：{top['topic']}（{top['priority']}，评分 {top['final_score']}）。"


def _normalize_item(item: Dict[str, Any]) -> Dict[str, Any]:
    text = " ".join(str(item.get(key, "")) for key in ("title", "summary", "content"))
    normalized = dict(item)
    normalized.setdefault("source", "unknown")
    normalized.setdefault("title", compact_text(text, 60) or "未命名信息源")
    normalized.setdefault("summary", text)
    if not normalized.get("city"):
        normalized["city"] = infer_city(text)
    if not normalized.get("company"):
        normalized["company"] = infer_company(text)
    return normalized


def _pipeline_warnings(
    original_items: List[Any],
    normalized_items: List[Dict[str, Any]],
    topics: List[Dict[str, Any]],
) -> List[str]:
    warnings = []
    dropped = len(original_items) - len(normalized_items)
    if dropped:
        warnings.append(f"已忽略 {dropped} 条非对象输入。")
    if normalized_items and not topics:
        warnings.append("未命中规则库，可补充政策、公告、土地、融资、城市更新或物业服务关键词。")
    return warnings
