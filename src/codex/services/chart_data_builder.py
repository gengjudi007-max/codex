from __future__ import annotations

from typing import Any, Dict, List


def build_city_ranking_chart_data(divergence_ranking: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "title": "城市分化指数排行榜",
        "x": [item.get("city") for item in divergence_ranking],
        "y": [item.get("divergence_index") for item in divergence_ranking],
        "series": "城市分化指数",
    }


def build_floor_price_chart_data(city_summary: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "title": "城市平均楼面价",
        "x": [item.get("city") for item in city_summary],
        "y": [round(item.get("avg_floor_price") or 0, 2) for item in city_summary],
        "series": "平均楼面价",
    }
