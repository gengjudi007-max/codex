from __future__ import annotations

from collections import Counter
from typing import Dict, List

from codex.classifiers.company_ownership_classifier import classify_land_buyer


STRUCTURE_SIGNALS = {
    "city_investment_decline": "城投拿地占比下降",
    "private_return": "民企重新进入土地市场",
    "core_heat_up": "核心城市土地热度上升",
}


def analyze_land_structure(records: List[Dict]) -> Dict:
    ownership_counter = Counter()

    for item in records:
        raw = item.get("raw") or {}
        result = classify_land_buyer(raw)
        ownership_counter[result["ownership"]] += 1

    total = sum(ownership_counter.values()) or 1

    ratios = {
        key: round(value / total * 100, 2)
        for key, value in ownership_counter.items()
    }

    signals = []

    city_investment_ratio = ratios.get("city_investment", 0)
    private_ratio = ratios.get("private", 0)

    if city_investment_ratio < 50:
        signals.append({
            "type": "city_investment_decline",
            "signal": STRUCTURE_SIGNALS["city_investment_decline"],
            "value": city_investment_ratio,
        })

    if private_ratio > 15:
        signals.append({
            "type": "private_return",
            "signal": STRUCTURE_SIGNALS["private_return"],
            "value": private_ratio,
        })

    return {
        "ownership_counts": dict(ownership_counter),
        "ownership_ratios": ratios,
        "signals": signals,
    }
