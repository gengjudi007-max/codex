from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple


ASSET_LAYERS = [
    "老破小",
    "外围刚需",
    "普通次新",
    "改善次新",
    "学区房",
    "核心改善",
    "豪宅",
]

MICRO_SIGNAL_TYPES = [
    "price_decline",
    "transaction_drop",
    "discount_expansion",
    "listing_cycle_lengthening",
    "bargaining_space_expansion",
    "land_cooling",
    "policy_support",
    "developer_behavior_change",
]

TREND_TYPES = [
    "价值重构",
    "需求收缩",
    "价格体系重估",
    "政策传导受阻",
    "核心资产松动",
    "库存压力扩散",
    "土地市场降温传导",
]


@dataclass
class MicroSignal:
    """微观趋势信号。

    city: 城市
    period: 时间，如 2024、2025Q4、2026-05
    asset_layer: 资产层级，如 老破小、次新房、学区房
    signal_type: 信号类型，如 price_decline、discount_expansion
    strength: 信号强度，建议 -10 到 10；负数代表压力，正数代表修复
    evidence: 证据描述
    source: 来源
    verified: 是否核验
    metadata: 原始数据扩展字段
    """

    city: str
    period: str
    asset_layer: str
    signal_type: str
    strength: float
    evidence: str
    source: str
    verified: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TransmissionPath:
    """趋势传导路径。"""

    city: str
    trend_type: str
    path: List[str]
    periods: List[str]
    evidence: List[str]
    confidence: float
    writing_angle: str


@dataclass
class TrendEvolutionReport:
    city: str
    trend_type: str
    phase_shift: bool
    confidence: float
    transmissions: List[Dict[str, Any]]
    micro_signals: List[Dict[str, Any]]
    article_insertions: List[str]
    verification_gaps: List[str]


class TrendEvolutionEngine:
    """趋势演化识别引擎。

    目标：
    - 不只识别“某项数据涨跌”，而是识别微观信号是否沿资产层级、城市板块、市场链条扩散；
    - 判断是否出现“量变到质变”的迹象；
    - 将识别结果转化为可写入深度报道的小标题、段落和补证清单。
    """

    def analyze(self, signals: List[Dict[str, Any]], city: Optional[str] = None) -> Dict[str, Any]:
        normalized = [self._normalize_signal(item) for item in signals]
        if city:
            normalized = [item for item in normalized if item.city == city]

        grouped: Dict[str, List[MicroSignal]] = {}
        for signal in normalized:
            grouped.setdefault(signal.city, []).append(signal)

        reports = []
        for city_name, city_signals in grouped.items():
            reports.append(self._analyze_city(city_name, city_signals))

        return {
            "reports": [asdict(report) for report in reports],
            "summary": self._build_summary(reports),
        }

    def _analyze_city(self, city: str, signals: List[MicroSignal]) -> TrendEvolutionReport:
        transmissions = self._detect_transmissions(city, signals)
        phase_shift = self._detect_phase_shift(transmissions, signals)
        trend_type = self._dominant_trend_type(transmissions, signals)
        confidence = self._confidence(transmissions, signals)
        insertions = self._build_article_insertions(city, trend_type, phase_shift, transmissions)
        gaps = self._verification_gaps(signals, transmissions)

        return TrendEvolutionReport(
            city=city,
            trend_type=trend_type,
            phase_shift=phase_shift,
            confidence=confidence,
            transmissions=[asdict(item) for item in transmissions],
            micro_signals=[asdict(item) for item in signals],
            article_insertions=insertions,
            verification_gaps=gaps,
        )

    def _detect_transmissions(self, city: str, signals: List[MicroSignal]) -> List[TransmissionPath]:
        paths: List[TransmissionPath] = []
        negative_signals = [item for item in signals if item.strength < 0]

        # 资产层级传导：弱资产 → 核心资产
        asset_path = self._ordered_asset_path(negative_signals)
        if len(asset_path) >= 2:
            evidence = [item.evidence for item in negative_signals if item.asset_layer in asset_path]
            periods = sorted({item.period for item in negative_signals if item.asset_layer in asset_path})
            trend_type = self._infer_asset_trend(asset_path)
            paths.append(
                TransmissionPath(
                    city=city,
                    trend_type=trend_type,
                    path=asset_path,
                    periods=periods,
                    evidence=evidence[:6],
                    confidence=self._path_confidence(asset_path, evidence, periods),
                    writing_angle=self._asset_writing_angle(city, asset_path, trend_type),
                )
            )

        # 市场链条传导：二手房 → 新房 / 价格 → 成交 / 土地 → 项目
        chain_paths = self._detect_market_chain_paths(city, signals)
        paths.extend(chain_paths)
        return paths

    def _ordered_asset_path(self, signals: List[MicroSignal]) -> List[str]:
        layers = []
        for layer in ASSET_LAYERS:
            if any(item.asset_layer == layer for item in signals):
                layers.append(layer)
        return layers

    def _detect_market_chain_paths(self, city: str, signals: List[MicroSignal]) -> List[TransmissionPath]:
        paths = []
        signal_types = {item.signal_type for item in signals if item.strength < 0}
        periods = sorted({item.period for item in signals})
        evidence = [item.evidence for item in signals if item.strength < 0][:6]

        if {"price_decline", "transaction_drop"}.issubset(signal_types):
            paths.append(
                TransmissionPath(
                    city=city,
                    trend_type="价格体系重估",
                    path=["价格调整", "成交变化"],
                    periods=periods,
                    evidence=evidence,
                    confidence=self._path_confidence(["价格调整", "成交变化"], evidence, periods),
                    writing_angle=f"{city}可写价格调整与成交变化之间的关系，重点核验成交是否集中在降价房源。",
                )
            )

        if {"land_cooling", "developer_behavior_change"}.issubset(signal_types):
            paths.append(
                TransmissionPath(
                    city=city,
                    trend_type="土地市场降温传导",
                    path=["土地降温", "房企行为变化", "项目供应变化"],
                    periods=periods,
                    evidence=evidence,
                    confidence=self._path_confidence(["土地降温", "房企行为变化", "项目供应变化"], evidence, periods),
                    writing_angle=f"{city}可写土地市场变化如何影响房企推盘、定价和项目节奏。",
                )
            )

        if "policy_support" in {item.signal_type for item in signals if item.strength > 0} and "transaction_drop" in signal_types:
            paths.append(
                TransmissionPath(
                    city=city,
                    trend_type="政策传导受阻",
                    path=["政策优化", "成交未同步修复"],
                    periods=periods,
                    evidence=evidence,
                    confidence=self._path_confidence(["政策优化", "成交未同步修复"], evidence, periods),
                    writing_angle=f"{city}可写政策优化后的市场传导效果，重点区分改善需求和刚需反应。",
                )
            )
        return paths

    def _detect_phase_shift(self, transmissions: List[TransmissionPath], signals: List[MicroSignal]) -> bool:
        crossed_layers = any(len(path.path) >= 3 for path in transmissions)
        crossed_markets = any(
            path.trend_type in ["价格体系重估", "政策传导受阻", "土地市场降温传导"]
            for path in transmissions
        )
        verified_count = sum(1 for item in signals if item.verified)
        repeated_periods = len({item.period for item in signals}) >= 2
        return (crossed_layers and repeated_periods) or (crossed_markets and verified_count >= 2)

    def _dominant_trend_type(self, transmissions: List[TransmissionPath], signals: List[MicroSignal]) -> str:
        if transmissions:
            ranked = sorted(transmissions, key=lambda item: item.confidence, reverse=True)
            return ranked[0].trend_type
        if any(item.signal_type == "price_decline" for item in signals):
            return "价格体系重估"
        if any(item.signal_type == "transaction_drop" for item in signals):
            return "需求收缩"
        return "价值重构"

    def _confidence(self, transmissions: List[TransmissionPath], signals: List[MicroSignal]) -> float:
        if not signals:
            return 0.0
        base = sum(item.confidence for item in transmissions) / len(transmissions) if transmissions else 0.2
        verified_bonus = min(sum(1 for item in signals if item.verified) * 0.08, 0.3)
        source_bonus = min(len({item.source for item in signals}) * 0.05, 0.2)
        return round(min(base + verified_bonus + source_bonus, 1.0), 2)

    def _verification_gaps(self, signals: List[MicroSignal], transmissions: List[TransmissionPath]) -> List[str]:
        gaps = []
        if not signals:
            return ["缺少微观信号数据。"]
        if sum(1 for item in signals if item.verified) < 2:
            gaps.append("已核验信号不足，建议补充政府网签、机构数据或项目采访核验。")
        if len({item.period for item in signals}) < 2:
            gaps.append("时间序列不足，建议至少补充两个以上时期的数据以判断传导。")
        if not transmissions:
            gaps.append("尚未形成明确传导路径，建议补充资产层级或市场链条数据。")
        if len({item.source for item in signals}) < 2:
            gaps.append("来源较单一，建议使用政府、机构、平台或采访材料交叉验证。")
        return gaps

    def _build_article_insertions(
        self,
        city: str,
        trend_type: str,
        phase_shift: bool,
        transmissions: List[TransmissionPath],
    ) -> List[str]:
        insertions = []
        for path in transmissions[:3]:
            path_text = " → ".join(path.path)
            if phase_shift:
                insertions.append(
                    f"{city}的相关信号显示，变化已沿着“{path_text}”路径扩散。该变化暂不宜简单概括为市场转向，仍需结合成交、价格和项目样本继续核验。"
                )
            else:
                insertions.append(
                    f"{city}出现“{path_text}”的阶段性变化。现有证据更多指向局部调整，尚不足以判断为趋势性变化。"
                )
        if not insertions:
            insertions.append(f"{city}当前微观信号尚未形成稳定传导路径，后续需继续跟踪{trend_type}相关数据。")
        return insertions

    def _infer_asset_trend(self, asset_path: List[str]) -> str:
        if any(layer in asset_path for layer in ["学区房", "核心改善", "豪宅"]):
            return "核心资产松动"
        if len(asset_path) >= 3:
            return "价值重构"
        return "价格体系重估"

    def _asset_writing_angle(self, city: str, asset_path: List[str], trend_type: str) -> str:
        return f"{city}可围绕“{' → '.join(asset_path)}”写{trend_type}，重点核验价格调整是否从弱资产向核心资产传导。"

    def _path_confidence(self, path: List[str], evidence: List[str], periods: List[str]) -> float:
        score = 0.25
        score += min(len(path) * 0.12, 0.35)
        score += min(len(evidence) * 0.04, 0.2)
        score += 0.2 if len(periods) >= 2 else 0
        return round(min(score, 1.0), 2)

    def _build_summary(self, reports: List[TrendEvolutionReport]) -> str:
        if not reports:
            return "暂无趋势演化信号。"
        fragments = []
        for report in reports:
            status = "出现质变迹象" if report.phase_shift else "仍处于阶段性变化"
            fragments.append(f"{report.city}：{report.trend_type}，{status}，置信度{report.confidence}")
        return "；".join(fragments) + "。"

    def _normalize_signal(self, item: Dict[str, Any]) -> MicroSignal:
        return MicroSignal(
            city=item.get("city", "未知城市"),
            period=str(item.get("period", "unknown")),
            asset_layer=item.get("asset_layer", "未知资产"),
            signal_type=item.get("signal_type", "price_decline"),
            strength=float(item.get("strength", 0)),
            evidence=item.get("evidence", ""),
            source=item.get("source", "unknown"),
            verified=bool(item.get("verified", False)),
            metadata=item.get("metadata", {}),
        )


def build_trend_signals_from_city_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """从城市数据库记录中提取趋势信号。

    该函数只做保守映射：
    - 价格同比/环比下降 → price_decline；
    - 成交同比/环比下降 → transaction_drop；
    - 土地溢价下降/流拍/城投占比高 → land_cooling；
    - 政策记录 → policy_support。
    """
    signals = []
    for record in records:
        dimension = record.get("dimension")
        metric = str(record.get("metric", ""))
        city = record.get("city", "未知城市")
        period = record.get("period", "unknown")
        source = record.get("source", "unknown")
        verified = bool(record.get("verified", False))
        yoy = _as_float(record.get("yoy"))
        mom = _as_float(record.get("mom"))
        value = _as_float(record.get("value"))
        asset_layer = infer_asset_layer(metric, record.get("raw_text", ""))

        if dimension == "price" and ((yoy is not None and yoy < 0) or (mom is not None and mom < 0)):
            signals.append(_signal(city, period, asset_layer, "price_decline", yoy or mom or -1, record, source, verified))
        elif dimension in ["transaction", "secondhand_market"] and ((yoy is not None and yoy < 0) or (mom is not None and mom < 0)):
            signals.append(_signal(city, period, asset_layer, "transaction_drop", yoy or mom or -1, record, source, verified))
        elif dimension == "land" and any(k in metric for k in ["流拍", "failed", "城投", "city_investment", "溢价"]):
            strength = -abs(value or yoy or mom or 1)
            signals.append(_signal(city, period, "土地", "land_cooling", strength, record, source, verified))
        elif dimension == "policy":
            signals.append(_signal(city, period, "政策", "policy_support", 2, record, source, verified))
    return signals


def infer_asset_layer(metric: str, raw_text: str = "") -> str:
    text = f"{metric} {raw_text}"
    for layer in ASSET_LAYERS:
        if layer in text:
            return layer
    if "学区" in text:
        return "学区房"
    if "次新" in text:
        return "普通次新"
    if "老旧" in text or "老破小" in text:
        return "老破小"
    if "豪宅" in text or "高端" in text:
        return "豪宅"
    if "改善" in text:
        return "改善次新"
    return "未知资产"


def render_trend_report_for_article(report: Dict[str, Any]) -> str:
    """将趋势演化报告转为稿件可用段落。"""
    city = report.get("city")
    trend_type = report.get("trend_type")
    phase_shift = report.get("phase_shift")
    confidence = report.get("confidence")
    insertions = report.get("article_insertions", [])
    paragraphs = []

    intro = f"{city}的微观信号被归入“{trend_type}”。"
    if phase_shift:
        intro += f"系统识别到跨层级或跨市场传导迹象，置信度为{confidence}。"
    else:
        intro += f"现有信号仍以阶段性变化为主，置信度为{confidence}。"
    paragraphs.append(intro)
    paragraphs.extend(insertions)

    gaps = report.get("verification_gaps", [])
    if gaps:
        paragraphs.append("发稿前仍需补充核验：" + "；".join(gaps) + "。")
    return "\n\n".join(paragraphs)


def _signal(
    city: str,
    period: str,
    asset_layer: str,
    signal_type: str,
    strength: float,
    record: Dict[str, Any],
    source: str,
    verified: bool,
) -> Dict[str, Any]:
    evidence = record.get("raw_text") or f"{record.get('metric')}出现变化，数值为{record.get('value')}。"
    return {
        "city": city,
        "period": period,
        "asset_layer": asset_layer,
        "signal_type": signal_type,
        "strength": strength,
        "evidence": evidence,
        "source": source,
        "verified": verified,
        "metadata": record,
    }


def _as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
