from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from codex.services.trend_evolution_engine import TrendEvolutionEngine


TRACKING_STATUS = ["active", "watch", "resolved", "paused"]


@dataclass
class TrendTrack:
    """长期趋势跟踪主题。

    示例：
    - 北京二手房价格调整从老破小向学区房扩散
    - 城投拿地从托底转向收缩
    - 物业公司从规模扩张转向主动退出低效项目
    """

    track_id: str
    title: str
    topic_tags: List[str]
    cities: List[str]
    asset_layers: List[str]
    trend_type: str
    created_at: str
    updated_at: str
    status: str = "active"
    hypothesis: Optional[str] = None
    evidence: Optional[List[Dict[str, Any]]] = None
    milestones: Optional[List[Dict[str, Any]]] = None
    next_watch_points: Optional[List[str]] = None
    editorial_notes: Optional[List[str]] = None


class TrendTrackingSystem:
    """趋势跟踪系统。

    核心能力：
    1. 创建长期趋势跟踪主题；
    2. 持续追加微观信号；
    3. 调用趋势演化引擎判断传导路径和质变信号；
    4. 自动生成阶段性选题、采访方向和连续报道计划。
    """

    def __init__(self) -> None:
        self.tracks: Dict[str, TrendTrack] = {}
        self.engine = TrendEvolutionEngine()

    def create_track(
        self,
        title: str,
        topic_tags: List[str],
        cities: List[str],
        asset_layers: List[str],
        trend_type: str,
        hypothesis: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = _today()
        track_id = _make_track_id(title, cities, trend_type)
        track = TrendTrack(
            track_id=track_id,
            title=title,
            topic_tags=topic_tags,
            cities=cities,
            asset_layers=asset_layers,
            trend_type=trend_type,
            created_at=now,
            updated_at=now,
            hypothesis=hypothesis,
            evidence=[],
            milestones=[],
            next_watch_points=[],
            editorial_notes=[],
        )
        self.tracks[track_id] = track
        return asdict(track)

    def add_signals(self, track_id: str, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        track = self._get_track(track_id)
        evidence = track.evidence or []
        evidence.extend(signals)
        track.evidence = evidence
        track.updated_at = _today()
        self.tracks[track_id] = track
        return self.evaluate_track(track_id)

    def evaluate_track(self, track_id: str) -> Dict[str, Any]:
        track = self._get_track(track_id)
        signals = track.evidence or []
        evolution = self.engine.analyze(signals)
        milestone = self._build_milestone(track, evolution)

        milestones = track.milestones or []
        milestones.append(milestone)
        track.milestones = milestones[-20:]
        track.next_watch_points = self._next_watch_points(track, evolution)
        track.editorial_notes = self._editorial_notes(track, evolution)
        track.status = self._status(track, evolution)
        track.updated_at = _today()
        self.tracks[track_id] = track

        return {
            "track": asdict(track),
            "evolution": evolution,
            "storyline_plan": self.build_storyline_plan(track_id),
        }

    def build_storyline_plan(self, track_id: str) -> Dict[str, Any]:
        track = self._get_track(track_id)
        latest = (track.milestones or [])[-1] if track.milestones else {}
        phase_shift = latest.get("phase_shift", False)
        confidence = latest.get("confidence", 0)

        if phase_shift and confidence >= 0.65:
            priority = "重点深度稿"
        elif confidence >= 0.45:
            priority = "跟踪报道"
        else:
            priority = "线索观察"

        return {
            "track_title": track.title,
            "priority": priority,
            "recommended_formats": self._recommended_formats(phase_shift, confidence),
            "story_angles": self._story_angles(track, latest),
            "interview_targets": self._interview_targets(track),
            "data_to_collect": self._data_to_collect(track),
            "publishing_cadence": self._publishing_cadence(priority),
        }

    def list_tracks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        rows = []
        for track in self.tracks.values():
            if status and track.status != status:
                continue
            rows.append(asdict(track))
        return sorted(rows, key=lambda item: item.get("updated_at", ""), reverse=True)

    def build_tracking_briefing(self) -> Dict[str, Any]:
        active = self.list_tracks(status="active")
        watch = self.list_tracks(status="watch")
        return {
            "date": _today(),
            "active_tracks": active,
            "watch_tracks": watch,
            "editorial_focus": self._editorial_focus(active, watch),
        }

    def _get_track(self, track_id: str) -> TrendTrack:
        if track_id not in self.tracks:
            raise KeyError(f"Trend track not found: {track_id}")
        return self.tracks[track_id]

    def _build_milestone(self, track: TrendTrack, evolution: Dict[str, Any]) -> Dict[str, Any]:
        reports = evolution.get("reports", [])
        phase_shift = any(report.get("phase_shift") for report in reports)
        confidence = max([report.get("confidence", 0) for report in reports], default=0)
        trend_types = list({report.get("trend_type") for report in reports if report.get("trend_type")})
        return {
            "date": _today(),
            "phase_shift": phase_shift,
            "confidence": confidence,
            "trend_types": trend_types,
            "summary": evolution.get("summary"),
            "evidence_count": len(track.evidence or []),
        }

    def _next_watch_points(self, track: TrendTrack, evolution: Dict[str, Any]) -> List[str]:
        points = []
        for city in track.cities:
            points.extend([
                f"{city}成交套数、成交面积是否继续变化",
                f"{city}不同资产层级价格是否继续传导",
                f"{city}挂牌量、议价空间和成交周期是否变化",
            ])
        if "土地" in track.topic_tags or "城投" in track.topic_tags:
            points.extend(["土地溢价率和流拍率", "城投拿地占比", "专项债收储项目变化"])
        if "政策" in track.topic_tags:
            points.extend(["政策发布后1周、1个月、3个月成交变化", "不同人群对政策的反应"])
        return list(dict.fromkeys(points))[:12]

    def _editorial_notes(self, track: TrendTrack, evolution: Dict[str, Any]) -> List[str]:
        notes = []
        reports = evolution.get("reports", [])
        if not reports:
            return ["尚无足够信号形成趋势判断。"]
        if any(report.get("phase_shift") for report in reports):
            notes.append("已出现跨层级或跨市场传导迹象，可考虑启动深度稿。")
        else:
            notes.append("当前仍以阶段性信号为主，建议继续跟踪，不宜过早定性。")
        gaps = []
        for report in reports:
            gaps.extend(report.get("verification_gaps", []))
        if gaps:
            notes.append("核验缺口：" + "；".join(list(dict.fromkeys(gaps))[:4]))
        return notes

    def _status(self, track: TrendTrack, evolution: Dict[str, Any]) -> str:
        reports = evolution.get("reports", [])
        if any(report.get("phase_shift") for report in reports):
            return "active"
        confidence = max([report.get("confidence", 0) for report in reports], default=0)
        if confidence >= 0.35:
            return "watch"
        return "watch"

    def _recommended_formats(self, phase_shift: bool, confidence: float) -> List[str]:
        if phase_shift and confidence >= 0.65:
            return ["深度报道", "数据图解", "采访稿", "评论版"]
        if confidence >= 0.45:
            return ["观察稿", "数据短稿", "采访提纲"]
        return ["线索备忘", "数据跟踪表"]

    def _story_angles(self, track: TrendTrack, latest: Dict[str, Any]) -> List[str]:
        base = []
        if track.trend_type == "价值重构":
            base.extend([
                "资产抗跌性与真实价值是否重新匹配",
                "价格调整是否从弱资产向核心资产扩散",
                "购房者定价逻辑如何变化",
            ])
        elif track.trend_type == "需求收缩":
            base.extend([
                "成交变化是否来自需求减少还是价格筛选",
                "刚需、改善和投资性需求的变化",
                "政策对需求释放的传导效果",
            ])
        else:
            base.extend([
                f"{track.title}的阶段性变化",
                "微观信号如何演化为结构变化",
                "哪些数据仍需核验",
            ])
        if latest.get("phase_shift"):
            base.insert(0, "量变是否已经形成质变信号")
        return base

    def _interview_targets(self, track: TrendTrack) -> List[str]:
        targets = ["中介经纪人", "项目销售人员", "购房者", "机构分析师"]
        if "土地" in track.topic_tags:
            targets.extend(["土地市场研究员", "房企投资拓展人士"])
        if "政策" in track.topic_tags:
            targets.extend(["政策研究人士", "银行个贷人士"])
        return list(dict.fromkeys(targets))

    def _data_to_collect(self, track: TrendTrack) -> List[str]:
        data = [
            "新房成交套数和成交面积",
            "二手房成交套数和成交面积",
            "挂牌量、成交周期和议价空间",
            "不同资产层级价格变化",
            "典型项目来访、认购和折扣变化",
        ]
        if "土地" in track.topic_tags:
            data.extend(["土地成交金额", "溢价率", "流拍率", "城投拿地占比"])
        if "政策" in track.topic_tags:
            data.extend(["政策发布日期", "政策前后成交变化", "按购房群体拆分的交易变化"])
        return list(dict.fromkeys(data))

    def _publishing_cadence(self, priority: str) -> str:
        if priority == "重点深度稿":
            return "建议1周内形成深度稿，随后每月跟踪更新。"
        if priority == "跟踪报道":
            return "建议每周更新一次数据，出现新传导信号后启动报道。"
        return "建议作为线索池保留，每两周复查一次。"

    def _editorial_focus(self, active: List[Dict[str, Any]], watch: List[Dict[str, Any]]) -> List[str]:
        focus = []
        if active:
            focus.append("优先处理已出现质变迹象的趋势主题。")
        if watch:
            focus.append("跟踪观察类主题需补充时间序列和多来源核验。")
        if not focus:
            focus.append("当前暂无趋势跟踪主题。")
        return focus


def create_default_beijing_asset_track() -> Dict[str, Any]:
    """示例：北京资产价值重构跟踪主题。"""
    system = TrendTrackingSystem()
    return system.create_track(
        title="北京二手房价格调整从老破小向次新房、学区房传导",
        topic_tags=["北京", "二手房", "价格", "老破小", "次新房", "学区房"],
        cities=["北京"],
        asset_layers=["老破小", "普通次新", "学区房"],
        trend_type="价值重构",
        hypothesis="若价格调整从老破小逐步传导至次新房和学区房，可能说明资产抗跌性与真实居住价值正在重新匹配。",
    )


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _make_track_id(title: str, cities: List[str], trend_type: str) -> str:
    seed = f"{title}-{'-'.join(cities)}-{trend_type}"
    return "".join(ch if ch.isalnum() else "_" for ch in seed)[:100]
