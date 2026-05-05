from __future__ import annotations

from typing import Dict, List


CYCLE_RULES = {
    "recovery": ["高溢价", "民企回归", "成交回暖"],
    "downturn": ["城投托底", "流拍", "销售承压"],
    "divergence": ["城市分化", "核心区升温", "弱二线承压"],
}


def infer_market_cycle(text: str) -> Dict:
    matched = []

    for cycle, keywords in CYCLE_RULES.items():
        for keyword in keywords:
            if keyword in text:
                matched.append((cycle, keyword))

    if not matched:
        return {
            "cycle": "uncertain",
            "confidence": 0.3,
            "matched_keywords": [],
        }

    score = {}
    for cycle, keyword in matched:
        score[cycle] = score.get(cycle, 0) + 1

    final_cycle = sorted(score.items(), key=lambda x: x[1], reverse=True)[0][0]

    return {
        "cycle": final_cycle,
        "confidence": round(min(0.95, 0.5 + len(matched) * 0.1), 2),
        "matched_keywords": [m[1] for m in matched],
    }


def summarize_cycle_signals(texts: List[str]) -> Dict:
    results = [infer_market_cycle(text) for text in texts]

    summary = {}
    for item in results:
        cycle = item["cycle"]
        summary[cycle] = summary.get(cycle, 0) + 1

    return {
        "summary": summary,
        "details": results,
    }
