from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List


REQUIRED_FIELDS = ["city", "title"]


def run_land_quality_checks(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    duplicates = detect_duplicate_titles(items)
    missing_required = detect_missing_required(items)
    abnormal_prices = detect_abnormal_floor_prices(items)

    return {
        "total": len(items),
        "duplicate_titles": duplicates,
        "missing_required": missing_required,
        "abnormal_floor_prices": abnormal_prices,
        "passed": not duplicates and not missing_required,
    }


def detect_duplicate_titles(items: List[Dict[str, Any]]) -> List[str]:
    titles = [item.get("title") for item in items if item.get("title")]
    counts = Counter(titles)
    return [title for title, count in counts.items() if count > 1]


def detect_missing_required(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for idx, item in enumerate(items):
        missing = [field for field in REQUIRED_FIELDS if not item.get(field)]
        if missing:
            results.append({
                "index": idx,
                "missing": missing,
                "title": item.get("title"),
            })
    return results


def detect_abnormal_floor_prices(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for item in items:
        metrics = item.get("metrics") or {}
        floor_price = metrics.get("floor_price")
        if floor_price is None:
            continue
        if floor_price <= 0 or floor_price > 500000:
            results.append({
                "title": item.get("title"),
                "floor_price": floor_price,
            })
    return results
