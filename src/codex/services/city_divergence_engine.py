from __future__ import annotations

from typing import Any, Dict, List


class CityDivergenceEngine:
    """城市分化分析引擎。"""

    def analyze(self, city_profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for profile in city_profiles:
            score = self._score_city(profile)
            label = self._classify(score)
            results.append(
                {
                    "city": profile.get("city"),
                    "score": score,
                    "label": label,
                    "signals": self._extract_signals(profile),
                }
            )

        results.sort(key=lambda x: x["score"], reverse=True)
        return {
            "ranking": results,
            "summary": self._build_summary(results),
        }

    def _score_city(self, profile: Dict[str, Any]) -> float:
        score = 0.0

        # 成交维度
        for item in profile.get("dimensions", {}).get("transaction", []):
            if item.get("yoy"):
                score += item.get("yoy", 0) * 0.3

        # 价格维度
        for item in profile.get("dimensions", {}).get("price", []):
            if item.get("mom"):
                score += item.get("mom", 0) * 0.2

        # 土地市场
        for item in profile.get("dimensions", {}).get("land", []):
            if item.get("value"):
                score += 1.0

        # 政策支持
        if profile.get("dimensions", {}).get("policy"):
            score += 1.5

        return score

    def _classify(self, score: float) -> str:
        if score > 10:
            return "恢复型"
        if score > 5:
            return "分化型"
        if score > 0:
            return "托底型"
        return "风险型"

    def _extract_signals(self, profile: Dict[str, Any]) -> List[str]:
        signals = []
        if profile.get("dimensions", {}).get("transaction"):
            signals.append("成交数据存在")
        if profile.get("dimensions", {}).get("price"):
            signals.append("价格数据存在")
        if profile.get("dimensions", {}).get("policy"):
            signals.append("政策信号存在")
        return signals

    def _build_summary(self, results: List[Dict[str, Any]]) -> str:
        if not results:
            return "暂无城市数据"
        top = results[0]
        bottom = results[-1]
        return f"表现最强城市：{top['city']}；相对较弱城市：{bottom['city']}。"
