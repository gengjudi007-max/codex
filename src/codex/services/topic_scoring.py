from typing import Any, Dict, List


PRIORITY_LABELS = {
    "A": "重点选题",
    "B": "可操作选题",
    "C": "跟踪选题",
}


def score_topics(topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """为房地产报道选题增加新闻优先级评分。"""
    scored = []
    for topic in topics:
        base_score = int(topic.get("score", 60))
        news_value = _score_news_value(topic)
        data_value = _score_data_value(topic)
        impact_value = _score_impact(topic)
        interview_value = _score_interviewability(topic)
        exclusivity_value = _score_exclusivity(topic)

        final_score = round(
            base_score * 0.35
            + news_value * 0.25
            + impact_value * 0.20
            + interview_value * 0.10
            + exclusivity_value * 0.10,
            2,
        )

        enriched = dict(topic)
        enriched["final_score"] = final_score
        enriched["priority"] = _priority(final_score)
        enriched["score_breakdown"] = {
            "base_score": base_score,
            "news_value": news_value,
            "data_value": data_value,
            "impact_value": impact_value,
            "interviewability": interview_value,
            "exclusivity": exclusivity_value,
        }
        scored.append(enriched)

    return sorted(scored, key=lambda item: item["final_score"], reverse=True)


def _score_news_value(topic: Dict[str, Any]) -> int:
    category = topic.get("category", "")
    trigger = str(topic.get("trigger", ""))
    if category in ["政策解读", "土地市场"]:
        return 90
    if "净利润" in trigger or "亏损" in trigger or "减值" in trigger:
        return 85
    return 70


def _score_data_value(topic: Dict[str, Any]) -> int:
    text = str(topic)
    if any(keyword in text for keyword in ["同比", "占比", "金额", "面积", "利润", "减值"]):
        return 85
    return 65


def _score_impact(topic: Dict[str, Any]) -> int:
    category = topic.get("category", "")
    if category in ["政策解读", "土地市场", "房企经营"]:
        return 88
    return 72


def _score_interviewability(topic: Dict[str, Any]) -> int:
    targets = topic.get("interview_targets", [])
    questions = topic.get("questions", [])
    score = 60
    if len(targets) >= 3:
        score += 15
    if len(questions) >= 3:
        score += 10
    return min(score, 90)


def _score_exclusivity(topic: Dict[str, Any]) -> int:
    text = str(topic)
    if any(keyword in text for keyword in ["专项债", "城投", "收储", "政策语义", "减值"]):
        return 82
    return 65


def _priority(score: float) -> str:
    if score >= 85:
        return PRIORITY_LABELS["A"]
    if score >= 72:
        return PRIORITY_LABELS["B"]
    return PRIORITY_LABELS["C"]
