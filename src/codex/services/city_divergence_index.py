from __future__ import annotations

from typing import Any, Dict, List


DEFAULT_WEIGHTS = {
    "land_count": 0.2,
    "avg_floor_price": 0.3,
    "avg_premium_rate": 0.2,
    "total_land_amount": 0.2,
    "total_planned_gfa": 0.1,
}


def compute_city_divergence_index(city_summary: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not city_summary:
        return []

    max_values = {}
    for field in DEFAULT_WEIGHTS:
        values = [item.get(field) or 0 for item in city_summary]
        max_values[field] = max(values) or 1

    results = []
    for item in city_summary:
        score = 0.0
        components = {}
        for field, weight in DEFAULT_WEIGHTS.items():
            value = item.get(field) or 0
            normalized = value / max_values[field] if max_values[field] else 0
            component = normalized * weight * 100
            components[field] = round(component, 2)
            score += component

        results.append({
            "city": item.get("city"),
            "divergence_index": round(score, 2),
            "components": components,
            "summary": item,
        })

    results.sort(key=lambda x: x["divergence_index"], reverse=True)
    return results
