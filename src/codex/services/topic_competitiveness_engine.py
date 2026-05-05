from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class TopicCompetitivenessResult:
    topic: str
    score: float
    level: str
    go_no_go: str
    competition_density: str
    recommended_type: str
    core_reason: str
    dimension_scores: Dict[str, float]
    differentiation_angles: List[str]
    kill_angles: List[str]
    required_evidence: List[str]
    interview_targets: List[str]


class TopicCompetitivenessEngine:
    """选题竞争力评估系统。

    评价重点：
    1. 信息增量：是否有新数据、新政策、新公告、新异常；
    2. 结构价值：是否能解释行业结构变化；
    3. 趋势潜力：是否存在跨时间、跨主体、跨层级传导；
    4. 可验证性：是否能用白名单数据和采访支撑；
    5. 竞争密度：是否容易被同质化报道覆盖。
    """

    def evaluate(
        self,
        topic: str,
        signals: Optional[List[Dict[str, Any]]] = None,
        data_scope: Optional[Dict[str, Any]] = None,
        source_count: int = 0,
    ) -> Dict[str, Any]:
        signals = signals or []
        data_scope = data_scope or {}

        dimension_scores = {
            "information_gain": self._information_gain(topic, signals),
            "structural_value": self._structural_value(topic, signals, data_scope),
            "trend_potential": self._trend_potential(signals, data_scope),
            "verifiability": self._verifiability(signals, data_scope, source_count),
            "competition_density": self._competition_density(topic, signals),
        }
        score = self._score(dimension_scores)
        level = self._level(score)
        go_no_go = "GO" if score >= 50 else "NO_GO"
        recommended_type = self._recommended_type(score, topic, signals, data_scope)

        result = TopicCompetitivenessResult(
            topic=topic,
            score=round(score, 2),
            level=level,
            go_no_go=go_no_go,
            competition_density=self._competition_label(dimension_scores["competition_density"]),
            recommended_type=recommended_type,
            core_reason=self._core_reason(level, dimension_scores),
            dimension_scores=dimension_scores,
            differentiation_angles=self._differentiation_angles(topic, signals, data_scope),
            kill_angles=self._kill_angles(topic),
            required_evidence=self._required_evidence(topic, signals, data_scope),
            interview_targets=self._interview_targets(topic, data_scope),
        )
        return asdict(result)

    def _information_gain(self, topic: str, signals: List[Dict[str, Any]]) -> float:
        score = 40.0
        if any(k in topic for k in ["最新", "首次", "新政", "公告", "年报", "业绩", "成交", "价格", "土地"]):
            score += 20
        if signals:
            score += min(len(signals) * 6, 25)
        if any(item.get("is_new") for item in signals):
            score += 15
        return min(score, 100)

    def _structural_value(self, topic: str, signals: List[Dict[str, Any]], data_scope: Dict[str, Any]) -> float:
        score = 35.0
        if any(k in topic for k in ["分化", "结构", "利润来源", "行为", "路径", "传导", "重构"]):
            score += 30
        if len(data_scope.get("cities", []) or []) >= 2 or len(data_scope.get("companies", []) or []) >= 2:
            score += 20
        if len({item.get("asset_layer") for item in signals if item.get("asset_layer")}) >= 2:
            score += 15
        return min(score, 100)

    def _trend_potential(self, signals: List[Dict[str, Any]], data_scope: Dict[str, Any]) -> float:
        score = 30.0
        periods = {item.get("period") for item in signals if item.get("period")}
        signal_types = {item.get("signal_type") for item in signals if item.get("signal_type")}
        asset_layers = {item.get("asset_layer") for item in signals if item.get("asset_layer")}
        if len(periods) >= 2:
            score += 25
        if len(signal_types) >= 2:
            score += 20
        if len(asset_layers) >= 2:
            score += 20
        if data_scope.get("tracking_topic"):
            score += 15
        return min(score, 100)

    def _verifiability(self, signals: List[Dict[str, Any]], data_scope: Dict[str, Any], source_count: int) -> float:
        score = 30.0
        verified = sum(1 for item in signals if item.get("verified"))
        score += min(verified * 10, 30)
        score += min(source_count * 8, 25)
        if data_scope.get("has_official_data"):
            score += 20
        if data_scope.get("has_interviews"):
            score += 10
        return min(score, 100)

    def _competition_density(self, topic: str, signals: List[Dict[str, Any]]) -> float:
        score = 30.0
        if any(k in topic for k in ["新政", "发布", "公告", "年报", "成交上涨", "成交下降"]):
            score += 25
        if any(k in topic for k in ["独家", "深层", "路径", "传导", "利润质量", "行为模式"]):
            score -= 15
        if len(signals) >= 4:
            score -= 8
        return max(min(score, 100), 0)

    def _score(self, scores: Dict[str, float]) -> float:
        return (
            scores["information_gain"] * 0.25
            + scores["structural_value"] * 0.25
            + scores["trend_potential"] * 0.20
            + scores["verifiability"] * 0.15
            - scores["competition_density"] * 0.15
        )

    def _level(self, score: float) -> str:
        if score >= 80:
            return "S"
        if score >= 65:
            return "A"
        if score >= 50:
            return "B"
        return "C"

    def _competition_label(self, score: float) -> str:
        if score >= 70:
            return "高"
        if score >= 40:
            return "中"
        return "低"

    def _recommended_type(self, score: float, topic: str, signals: List[Dict[str, Any]], data_scope: Dict[str, Any]) -> str:
        if score >= 80:
            return "深度报道"
        if "政策" in topic:
            return "政策解读"
        if len(data_scope.get("companies", []) or []) >= 2 or "Top10" in topic:
            return "数据榜单"
        if score >= 65:
            return "观察稿"
        if score >= 50:
            return "短新闻"
        return "线索备忘"

    def _core_reason(self, level: str, scores: Dict[str, float]) -> str:
        strongest = max(scores.items(), key=lambda item: item[1])[0]
        if level in ["S", "A"]:
            return f"该选题具备较强竞争力，主要优势来自{strongest}。"
        if level == "B":
            return "该选题可以作为补充报道，但需要补强结构价值或可验证材料。"
        return "该选题当前信息增量和结构价值不足，不建议启动长稿。"

    def _differentiation_angles(self, topic: str, signals: List[Dict[str, Any]], data_scope: Dict[str, Any]) -> List[str]:
        angles = []
        if len(data_scope.get("companies", []) or []) >= 2 or any(k in topic for k in ["房企", "利润", "年报"]):
            angles.extend(["利润来源结构差异", "企业行为路径差异", "利润质量与可持续性"])
        if len(data_scope.get("cities", []) or []) >= 2 or "城市" in topic:
            angles.extend(["城市分化路径", "成交、价格与库存的组合变化", "政策传导差异"])
        if len({item.get("asset_layer") for item in signals if item.get("asset_layer")}) >= 2:
            angles.extend(["资产层级传导", "抗跌性与真实价值匹配", "微观价格变化如何扩散"])
        if "土地" in topic or "拿地" in topic:
            angles.extend(["买方结构变化", "城投托底与资金闭环", "土地消化路径"])
        return list(dict.fromkeys(angles or ["机制解释", "结构对比", "后续跟踪变量"]))[:6]

    def _kill_angles(self, topic: str) -> List[str]:
        kill = ["简单复述公开信息", "只做数据排名不解释结构", "用未经核验采访替代事实"]
        if "利润" in topic or "年报" in topic:
            kill.append("只比较净利润高低")
        if "成交" in topic:
            kill.append("只写单日成交涨跌")
        if "政策" in topic:
            kill.append("把政策效果提前定性为回暖或反转")
        return kill

    def _required_evidence(self, topic: str, signals: List[Dict[str, Any]], data_scope: Dict[str, Any]) -> List[str]:
        evidence = ["白名单来源数据", "统计口径和发布时间", "至少一个交叉验证来源"]
        if "房企" in topic or data_scope.get("companies"):
            evidence.extend(["年报或业绩公告", "销售金额和销售面积", "毛利率、现金流和减值数据"])
        if "城市" in topic or data_scope.get("cities"):
            evidence.extend(["新房成交套数/面积", "二手房成交套数/面积", "价格和库存数据"])
        if "土地" in topic:
            evidence.extend(["土地成交金额", "溢价率", "买方结构"])
        if signals:
            evidence.append("微观信号对应的项目或采访材料")
        return list(dict.fromkeys(evidence))

    def _interview_targets(self, topic: str, data_scope: Dict[str, Any]) -> List[str]:
        targets = ["机构分析师"]
        if "房企" in topic or data_scope.get("companies"):
            targets.extend(["房企人士", "项目销售人员", "供应商或业主代表（需核验）"])
        if "城市" in topic or "楼市" in topic or data_scope.get("cities"):
            targets.extend(["中介经纪人", "购房者", "项目销售人员"])
        if "土地" in topic:
            targets.extend(["土地市场研究员", "房企投资拓展人士", "地方平台公司人士"])
        if "政策" in topic:
            targets.extend(["政策研究人士", "银行个贷人士"])
        return list(dict.fromkeys(targets))
