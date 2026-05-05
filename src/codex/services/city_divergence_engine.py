from __future__ import annotations

from typing import Any, Dict, List, Optional


CITY_LABELS = ["恢复型", "分化型", "托底型", "风险型"]


class CityDivergenceEngine:
    """城市分化分析引擎（增强版）。

    评分维度：
    1. 成交修复：新房、二手房成交面积/套数同比、环比；
    2. 价格韧性：新房、二手房价格环比/同比；
    3. 土地市场：溢价率、流拍率、城投拿地占比；
    4. 库存压力：去化周期、库存面积；
    5. 政策强度：限购、信贷、公积金、补贴等政策；
    6. 房企行为：推盘、拿地、促销、退出等活动。
    """

    def analyze(self, city_profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for profile in city_profiles:
            breakdown = self._score_breakdown(profile)
            score = round(sum(breakdown.values()), 2)
            label = self._classify(score, breakdown)
            results.append(
                {
                    "city": profile.get("city"),
                    "score": score,
                    "label": label,
                    "score_breakdown": breakdown,
                    "signals": self._extract_signals(profile, breakdown),
                    "data_gaps": profile.get("data_gaps", []),
                    "writing_angle": self._writing_angle(profile, label, breakdown),
                }
            )

        results.sort(key=lambda x: x["score"], reverse=True)
        return {
            "ranking": results,
            "groups": self._group_results(results),
            "summary": self._build_summary(results),
            "methodology": self._methodology(),
        }

    def _score_breakdown(self, profile: Dict[str, Any]) -> Dict[str, float]:
        return {
            "transaction": self._transaction_score(profile),
            "price": self._price_score(profile),
            "land": self._land_score(profile),
            "inventory": self._inventory_score(profile),
            "policy": self._policy_score(profile),
            "company_activity": self._company_activity_score(profile),
        }

    def _transaction_score(self, profile: Dict[str, Any]) -> float:
        score = 0.0
        items = profile.get("dimensions", {}).get("transaction", []) + profile.get("dimensions", {}).get("secondhand_market", [])
        for item in items:
            metric = str(item.get("metric", ""))
            yoy = _as_float(item.get("yoy"))
            mom = _as_float(item.get("mom"))
            value = _as_float(item.get("value"))
            if yoy is not None:
                weight = 0.35 if "secondhand" in metric or "二手" in metric else 0.3
                score += _cap(yoy * weight, -8, 10)
            if mom is not None:
                score += _cap(mom * 0.15, -4, 5)
            if value is not None and value > 0:
                score += 0.5
        return round(score, 2)

    def _price_score(self, profile: Dict[str, Any]) -> float:
        score = 0.0
        for item in profile.get("dimensions", {}).get("price", []):
            yoy = _as_float(item.get("yoy"))
            mom = _as_float(item.get("mom"))
            if yoy is not None:
                score += _cap(yoy * 0.25, -6, 6)
            if mom is not None:
                score += _cap(mom * 1.2, -5, 5)
        return round(score, 2)

    def _land_score(self, profile: Dict[str, Any]) -> float:
        score = 0.0
        for item in profile.get("dimensions", {}).get("land", []):
            metric = str(item.get("metric", ""))
            value = _as_float(item.get("value"))
            yoy = _as_float(item.get("yoy"))
            if value is None:
                continue
            if "premium" in metric or "溢价" in metric:
                score += _cap(value * 0.25, 0, 8)
            elif "failed" in metric or "流拍" in metric:
                score -= _cap(value * 0.25, 0, 8)
            elif "city_investment" in metric or "城投" in metric:
                score -= _cap(value * 0.18, 0, 10)
            elif "land_amount" in metric or "成交金额" in metric:
                score += 1.0
            if yoy is not None:
                score += _cap(yoy * 0.08, -3, 3)
        return round(score, 2)

    def _inventory_score(self, profile: Dict[str, Any]) -> float:
        score = 0.0
        for item in profile.get("dimensions", {}).get("inventory", []):
            metric = str(item.get("metric", ""))
            value = _as_float(item.get("value"))
            if value is None:
                continue
            if "months" in metric or "去化周期" in metric:
                if value <= 12:
                    score += 4
                elif value <= 18:
                    score += 1
                elif value <= 24:
                    score -= 3
                else:
                    score -= 6
            elif "inventory" in metric or "库存" in metric:
                yoy = _as_float(item.get("yoy"))
                if yoy is not None:
                    score -= _cap(yoy * 0.1, -3, 5)
        return round(score, 2)

    def _policy_score(self, profile: Dict[str, Any]) -> float:
        items = profile.get("dimensions", {}).get("policy", [])
        if not items:
            return 0.0
        score = 0.0
        for item in items:
            text = f"{item.get('metric', '')} {item.get('raw_text', '')}"
            if any(k in text for k in ["限购", "首付", "公积金", "房贷", "购房补贴", "卖旧买新"]):
                score += 1.5
            else:
                score += 0.5
        return round(min(score, 6), 2)

    def _company_activity_score(self, profile: Dict[str, Any]) -> float:
        score = 0.0
        for item in profile.get("dimensions", {}).get("company_activity", []):
            text = f"{item.get('metric', '')} {item.get('raw_text', '')}"
            if any(k in text for k in ["集中推盘", "认购", "来访", "开盘", "热销", "加推"]):
                score += 1.5
            if any(k in text for k in ["折扣", "特价", "优惠", "降价", "渠道"]):
                score -= 0.5
            if any(k in text for k in ["退出", "停工", "延期"]):
                score -= 2
        return round(score, 2)

    def _classify(self, score: float, breakdown: Dict[str, float]) -> str:
        land = breakdown.get("land", 0)
        transaction = breakdown.get("transaction", 0)
        price = breakdown.get("price", 0)
        inventory = breakdown.get("inventory", 0)

        if score >= 12 and transaction > 0 and price >= -1:
            return "恢复型"
        if transaction > 0 and (price < 0 or land < -3 or inventory < 0):
            return "分化型"
        if land <= -5 or (breakdown.get("policy", 0) > 0 and transaction <= 2):
            return "托底型"
        if score < 0 or inventory <= -4:
            return "风险型"
        return "分化型"

    def _extract_signals(self, profile: Dict[str, Any], breakdown: Dict[str, float]) -> List[str]:
        signals = []
        if breakdown.get("transaction", 0) > 3:
            signals.append("成交端出现修复信号")
        elif breakdown.get("transaction", 0) < 0:
            signals.append("成交端仍有压力")

        if breakdown.get("price", 0) > 1:
            signals.append("价格端表现相对稳定")
        elif breakdown.get("price", 0) < -1:
            signals.append("价格端仍承压")

        if breakdown.get("land", 0) > 2:
            signals.append("土地市场热度相对较高")
        elif breakdown.get("land", 0) < -3:
            signals.append("土地市场依赖托底或流拍压力较高")

        if breakdown.get("inventory", 0) < -3:
            signals.append("库存去化周期偏长")
        if breakdown.get("policy", 0) > 0:
            signals.append("近期有政策调整信号")
        if breakdown.get("company_activity", 0) > 0:
            signals.append("房企项目端活动增加")
        return signals or ["数据不足，暂不能形成明确判断"]

    def _writing_angle(self, profile: Dict[str, Any], label: str, breakdown: Dict[str, float]) -> str:
        city = profile.get("city")
        if label == "恢复型":
            return f"{city}可作为核心城市修复样本，重点写成交、价格和房企活动之间的关系。"
        if label == "分化型":
            return f"{city}适合写城市内部结构差异，重点区分核心区与外围、改善与刚需、新房与二手房。"
        if label == "托底型":
            return f"{city}适合写政策或城投托底下的市场运行，重点核验土地、成交和库存之间的关系。"
        return f"{city}适合写风险观察，重点关注成交下滑、价格压力、库存和企业项目退出。"

    def _group_results(self, results: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        groups = {label: [] for label in CITY_LABELS}
        for item in results:
            groups.setdefault(item["label"], []).append(item["city"])
        return groups

    def _build_summary(self, results: List[Dict[str, Any]]) -> str:
        if not results:
            return "暂无城市数据。"
        groups = self._group_results(results)
        fragments = []
        for label in CITY_LABELS:
            cities = groups.get(label, [])
            if cities:
                fragments.append(f"{label}城市包括：{'、'.join(cities)}")
        return "；".join(fragments) + "。"

    def _methodology(self) -> Dict[str, str]:
        return {
            "transaction": "根据新房、二手房成交套数/面积的同比、环比变化评分。",
            "price": "根据新房、二手房价格同比、环比变化评分。",
            "land": "根据土地溢价率、流拍率、城投拿地占比和土地成交变化评分。",
            "inventory": "根据库存和去化周期评分。",
            "policy": "根据限购、信贷、公积金、补贴、卖旧买新等政策信号评分。",
            "company_activity": "根据房企推盘、认购、折扣、项目退出等活动评分。",
        }


def _as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _cap(value: float, min_value: float, max_value: float) -> float:
    return max(min(value, max_value), min_value)
