from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List


SOURCE_WEIGHTS = {
    "level_1": 1.0,  # 官方、交易所、政府
    "level_2": 0.85, # 地方政府、官方平台
    "level_3": 0.65, # 中指/CRIC/Wind/同花顺/贝壳等第三方
    "unknown": 0.4,
}


def fuse_items_by_city(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped = defaultdict(list)
    for item in items:
        city = item.get("city") or "未知城市"
        grouped[city].append(item)

    fused = []
    for city, city_items in grouped.items():
        categories = defaultdict(int)
        source_scores = []
        for item in city_items:
            categories[item.get("category") or "unknown"] += 1
            source_level = item.get("source_level") or "unknown"
            source_scores.append(SOURCE_WEIGHTS.get(source_level, SOURCE_WEIGHTS["unknown"]))

        confidence = round(sum(source_scores) / len(source_scores), 2) if source_scores else 0
        fused.append({
            "city": city,
            "item_count": len(city_items),
            "categories": dict(categories),
            "source_confidence": confidence,
            "items": city_items,
        })

    return sorted(fused, key=lambda x: (x["source_confidence"], x["item_count"]), reverse=True)


def build_cross_source_signals(fused_city_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    signals = []
    for city_data in fused_city_items:
        city = city_data["city"]
        categories = city_data.get("categories", {})
        if categories.get("land", 0) and categories.get("transaction", 0):
            signals.append({
                "city": city,
                "type": "land_transaction_cross_signal",
                "signal": f"{city} 同时出现土地与成交数据，可进一步观察供需关系变化。",
                "confidence": city_data.get("source_confidence"),
            })
        if categories.get("policy", 0) and (categories.get("land", 0) or categories.get("transaction", 0)):
            signals.append({
                "city": city,
                "type": "policy_market_cross_signal",
                "signal": f"{city} 政策与市场数据同时出现更新，可进一步跟踪政策效果。",
                "confidence": city_data.get("source_confidence"),
            })
    return signals
