from __future__ import annotations

from typing import Dict, List


DEFAULT_STRUCTURE = [
    "导语",
    "市场变化",
    "企业行为",
    "城市分化",
    "行业趋势",
]


def build_story_outline(topic: str, signals: List[Dict], city_ranking: List[Dict]) -> Dict:
    return {
        "topic": topic,
        "structure": DEFAULT_STRUCTURE,
        "signals": signals[:10],
        "top_cities": city_ranking[:5],
    }


def generate_lead(topic: str, signals: List[Dict]) -> str:
    if signals:
        signal = signals[0].get("signal")
        return f"{signal}。在房地产市场持续分化背景下，{topic}正在出现新的变化。"
    return f"{topic}正在出现新的市场变化。"


def generate_market_section(city_ranking: List[Dict]) -> str:
    if not city_ranking:
        return "多个城市土地市场表现出现分化。"

    top = city_ranking[0]
    return (
        f"从城市分化指数来看，{top.get('city')}当前热度位居前列，"
        f"分化指数达到{top.get('divergence_index')}。"
    )


def generate_final_story(topic: str, signals: List[Dict], city_ranking: List[Dict]) -> Dict:
    outline = build_story_outline(topic, signals, city_ranking)

    article = {
        "title": topic,
        "lead": generate_lead(topic, signals),
        "market_section": generate_market_section(city_ranking),
        "outline": outline,
    }

    return article
