from __future__ import annotations

from typing import Any, Dict, List


HIGH_PREMIUM_THRESHOLD = 20
HIGH_FLOOR_PRICE_THRESHOLD = 50000


def detect_news_signals(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    signals = []

    for item in records:
        metrics = item.get("metrics") or {}
        floor_price = metrics.get("floor_price") or 0
        premium_rate = metrics.get("premium_rate") or 0
        title = item.get("title") or "未知地块"
        city = item.get("city") or "未知城市"

        if premium_rate >= HIGH_PREMIUM_THRESHOLD:
            signals.append({
                "type": "high_premium_rate",
                "city": city,
                "title": title,
                "value": premium_rate,
                "signal": f"{city} 出现高溢价地块，溢价率达到 {premium_rate}%",
            })

        if floor_price >= HIGH_FLOOR_PRICE_THRESHOLD:
            signals.append({
                "type": "high_floor_price",
                "city": city,
                "title": title,
                "value": floor_price,
                "signal": f"{city} 出现高楼面价地块，楼面价达到 {floor_price} 元/平方米",
            })

    return signals
