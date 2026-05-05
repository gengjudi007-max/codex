from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


ARTICLE_TYPES = [
    "快讯",
    "短新闻",
    "观察稿",
    "深度报道",
    "评论社论",
    "专题系列",
    "数据榜单",
    "公司分析",
    "政策解读",
]

MODEL_REGISTRY = {
    "data_validation": "数据核验与白名单来源检查",
    "topic_scoring": "选题评分",
    "policy_semantic": "政策语义变化识别",
    "announcement_parser": "上市公司公告解析",
    "land_anomaly": "土地市场异动识别",
    "city_divergence": "城市分化分析",
    "trend_evolution": "趋势演化识别",
    "trend_tracking": "趋势长期跟踪",
    "signal_inference": "迹象推理",
    "developer_behavior": "房企行为识别",
    "top10_comparison": "Top10房企横向对比",
    "field_reporting": "现场表达增强",
    "interview_store": "采访素材结构化调用",
    "anti_ai_writing": "去AI痕迹表达",
    "final_check": "终稿事实校验",
    "publisher": "最终成稿引擎",
    "visual_package": "榜单与图表输出",
}


@dataclass
class OrchestrationDecision:
    article_type: str
    primary_model: str
    support_models: List[str]
    suppressed_models: List[str]
    writing_strategy: str
    structure_suggestion: List[str]
    risk_level: str
    guardrails: List[str]
    reasons: List[str]


class ModelOrchestrator:
    """模型调度系统。

    原则：
    1. 单篇稿件只允许一个主模型；
    2. 支撑模型最多三个；
    3. 模型服务于稿件逻辑，不在稿件中显性展示；
    4. 高法律风险题材默认压制强判断模型；
    5. 没有跨时间、跨主体、跨层级信号时，不调用趋势模型。
    """

    def orchestrate(
        self,
        topic: str,
        article_type: Optional[str] = None,
        signals: Optional[List[Dict[str, Any]]] = None,
        data_scope: Optional[Dict[str, Any]] = None,
        risk_preference: str = "neutral",
    ) -> Dict[str, Any]:
        signals = signals or []
        data_scope = data_scope or {}
        resolved_type = article_type or self._infer_article_type(topic, signals, data_scope)
        risk_level = self._risk_level(topic, signals, risk_preference)

        decision = self._decision_by_type(resolved_type, topic, signals, data_scope, risk_level)
        return asdict(decision)

    def _decision_by_type(
        self,
        article_type: str,
        topic: str,
        signals: List[Dict[str, Any]],
        data_scope: Dict[str, Any],
        risk_level: str,
    ) -> OrchestrationDecision:
        complexity = self._complexity(signals, data_scope)
        is_company_topic = self._is_company_topic(topic, data_scope)
        is_city_topic = self._is_city_topic(topic, data_scope)
        is_policy_topic = "政策" in topic or article_type == "政策解读"
        is_land_topic = "土地" in topic or "拿地" in topic or "土拍" in topic
        has_time_series = self._has_time_series(signals)
        has_cross_subject = self._has_cross_subject(data_scope)
        has_chain_signal = self._has_chain_signal(signals)

        if article_type in ["快讯", "短新闻"]:
            return OrchestrationDecision(
                article_type=article_type,
                primary_model="data_validation",
                support_models=["topic_scoring", "final_check"],
                suppressed_models=self._suppress_except(["data_validation", "topic_scoring", "final_check"]),
                writing_strategy="只写事实、时间、主体、数据来源和下一步影响，不展开趋势、行为和分化分析。",
                structure_suggestion=["事实发生", "核心数据", "来源与背景"],
                risk_level=risk_level,
                guardrails=self._guardrails(article_type, risk_level),
                reasons=["快讯以时效和准确为先，不适合堆叠分析模型。"],
            )

        if article_type == "观察稿":
            primary = "signal_inference" if has_chain_signal else "city_divergence" if is_city_topic else "data_validation"
            support = ["data_validation", "field_reporting", "anti_ai_writing", "final_check"][:3]
            return OrchestrationDecision(
                article_type=article_type,
                primary_model=primary,
                support_models=support,
                suppressed_models=self._suppress_except([primary] + support),
                writing_strategy="围绕一个现象做轻解释，只保留一条主线，不展开完整因果链。",
                structure_suggestion=["现象", "一线表现", "待观察变量"],
                risk_level=risk_level,
                guardrails=self._guardrails(article_type, risk_level),
                reasons=["观察稿需要解释现象，但不宜做过重趋势判断。"],
            )

        if article_type == "深度报道":
            primary = self._select_depth_primary(topic, signals, data_scope)
            support = self._select_depth_support(primary, is_company_topic, is_city_topic, is_policy_topic, is_land_topic, has_time_series)
            return OrchestrationDecision(
                article_type=article_type,
                primary_model=primary,
                support_models=support,
                suppressed_models=self._suppress_except([primary] + support),
                writing_strategy="只设一个主逻辑，最多一条辅助链。以事实和采访推进，不把模型痕迹写进正文。",
                structure_suggestion=self._depth_structure(primary),
                risk_level=risk_level,
                guardrails=self._guardrails(article_type, risk_level),
                reasons=["深度报道需要机制解释，但单篇稿件必须控制模型数量。", f"主模型选择为{primary}，因为主题信号与其匹配。"],
            )

        if article_type == "评论社论":
            primary = "signal_inference" if has_chain_signal else "trend_evolution"
            support = ["data_validation", "anti_ai_writing", "final_check"]
            return OrchestrationDecision(
                article_type=article_type,
                primary_model=primary,
                support_models=support,
                suppressed_models=self._suppress_except([primary] + support),
                writing_strategy="用一个判断打穿全文，减少材料堆叠；事实用于支撑观点，不展开多组模型。",
                structure_suggestion=["问题提出", "核心判断", "事实支撑", "政策或行业含义"],
                risk_level=risk_level,
                guardrails=self._guardrails(article_type, risk_level),
                reasons=["评论稿强调判断力，不宜同时调用多个分析框架。"],
            )

        if article_type == "专题系列":
            return OrchestrationDecision(
                article_type=article_type,
                primary_model="trend_tracking",
                support_models=["data_validation", "interview_store", "publisher"],
                suppressed_models=self._suppress_except(["trend_tracking", "data_validation", "interview_store", "publisher"]),
                writing_strategy="专题层面可以容纳多个模型，但单篇只调用一个主模型；以连续报道计划拆分复杂逻辑。",
                structure_suggestion=["总题设计", "分篇计划", "数据跟踪表", "采访路线"],
                risk_level=risk_level,
                guardrails=self._guardrails(article_type, risk_level),
                reasons=["专题需要跨时间跟踪，趋势跟踪系统是主模型。"],
            )

        if article_type == "数据榜单":
            primary = "city_divergence" if is_city_topic else "top10_comparison" if is_company_topic else "data_validation"
            support = ["visual_package", "data_validation", "final_check"]
            return OrchestrationDecision(
                article_type=article_type,
                primary_model=primary,
                support_models=support,
                suppressed_models=self._suppress_except([primary] + support),
                writing_strategy="以榜单和口径说明为核心，正文只解释排序逻辑和关键差异，不做过度结论。",
                structure_suggestion=["榜单口径", "排名结果", "结构解释", "风险提示"],
                risk_level=risk_level,
                guardrails=self._guardrails(article_type, risk_level),
                reasons=["榜单稿需要模型生成排序，但必须突出数据口径。"],
            )

        if article_type == "公司分析":
            primary = "developer_behavior"
            support = ["announcement_parser", "data_validation", "final_check"]
            if has_cross_subject:
                support.insert(1, "top10_comparison")
            support = support[:3]
            return OrchestrationDecision(
                article_type=article_type,
                primary_model=primary,
                support_models=support,
                suppressed_models=self._suppress_except([primary] + support),
                writing_strategy="围绕利润来源、行为选择和后续约束展开，避免未经核验的品质、舆情和维权定性。",
                structure_suggestion=["业绩结果", "利润结构", "行为路径", "待核验影响"],
                risk_level=risk_level,
                guardrails=self._guardrails(article_type, risk_level),
                reasons=["公司稿件需要识别企业行为路径，房企行为模型为主模型。"],
            )

        if article_type == "政策解读":
            primary = "policy_semantic"
            support = ["data_validation", "field_reporting", "final_check"]
            return OrchestrationDecision(
                article_type=article_type,
                primary_model=primary,
                support_models=support,
                suppressed_models=self._suppress_except([primary] + support),
                writing_strategy="先还原政策文本变化，再写适用对象和执行路径；不把政策效果提前定性。",
                structure_suggestion=["政策原文", "语义变化", "影响对象", "执行观察"],
                risk_level=risk_level,
                guardrails=self._guardrails(article_type, risk_level),
                reasons=["政策稿必须以文本和执行口径为核心。"],
            )

        return OrchestrationDecision(
            article_type=article_type,
            primary_model="data_validation",
            support_models=["topic_scoring", "final_check"],
            suppressed_models=self._suppress_except(["data_validation", "topic_scoring", "final_check"]),
            writing_strategy="先核验事实，再决定是否升级为观察或深度报道。",
            structure_suggestion=["事实", "数据", "待补材料"],
            risk_level=risk_level,
            guardrails=self._guardrails(article_type, risk_level),
            reasons=["无法明确匹配稿件类型，默认采用保守模式。"],
        )

    def _select_depth_primary(self, topic: str, signals: List[Dict[str, Any]], data_scope: Dict[str, Any]) -> str:
        if self._is_company_topic(topic, data_scope):
            return "developer_behavior" if not self._has_cross_subject(data_scope) else "top10_comparison"
        if self._has_time_series(signals) and self._has_chain_signal(signals):
            return "trend_evolution"
        if self._is_city_topic(topic, data_scope):
            return "city_divergence"
        if "政策" in topic:
            return "policy_semantic"
        if "土地" in topic or "拿地" in topic:
            return "land_anomaly"
        return "signal_inference"

    def _select_depth_support(
        self,
        primary: str,
        is_company_topic: bool,
        is_city_topic: bool,
        is_policy_topic: bool,
        is_land_topic: bool,
        has_time_series: bool,
    ) -> List[str]:
        support = ["data_validation", "field_reporting", "final_check"]
        if primary != "trend_evolution" and has_time_series:
            support.insert(1, "trend_evolution")
        if primary != "developer_behavior" and is_company_topic:
            support.insert(1, "developer_behavior")
        if primary != "city_divergence" and is_city_topic:
            support.insert(1, "city_divergence")
        if primary != "policy_semantic" and is_policy_topic:
            support.insert(1, "policy_semantic")
        if primary != "land_anomaly" and is_land_topic:
            support.insert(1, "land_anomaly")
        return list(dict.fromkeys(support))[:3]

    def _infer_article_type(self, topic: str, signals: List[Dict[str, Any]], data_scope: Dict[str, Any]) -> str:
        if any(k in topic for k in ["快讯", "刚刚", "发布", "公告称"]):
            return "短新闻"
        if any(k in topic for k in ["评论", "社论", "怎么看"]):
            return "评论社论"
        if any(k in topic for k in ["专题", "系列", "跟踪"]):
            return "专题系列"
        if any(k in topic for k in ["榜单", "排名", "Top10", "十城"]):
            return "数据榜单"
        if self._is_company_topic(topic, data_scope):
            return "公司分析"
        if "政策" in topic:
            return "政策解读"
        if self._complexity(signals, data_scope) >= 5:
            return "深度报道"
        return "观察稿"

    def _complexity(self, signals: List[Dict[str, Any]], data_scope: Dict[str, Any]) -> int:
        score = 0
        score += min(len(signals), 3)
        score += 1 if self._has_time_series(signals) else 0
        score += 1 if self._has_cross_subject(data_scope) else 0
        score += 1 if len(data_scope.get("cities", []) or []) >= 2 else 0
        score += 1 if len(data_scope.get("companies", []) or []) >= 2 else 0
        return score

    def _has_time_series(self, signals: List[Dict[str, Any]]) -> bool:
        return len({str(item.get("period")) for item in signals if item.get("period")}) >= 2

    def _has_chain_signal(self, signals: List[Dict[str, Any]]) -> bool:
        types = {item.get("signal_type") for item in signals}
        layers = {item.get("asset_layer") for item in signals if item.get("asset_layer")}
        return len(types) >= 2 or len(layers) >= 2

    def _has_cross_subject(self, data_scope: Dict[str, Any]) -> bool:
        return len(data_scope.get("companies", []) or []) >= 2 or len(data_scope.get("cities", []) or []) >= 2

    def _is_company_topic(self, topic: str, data_scope: Dict[str, Any]) -> bool:
        return bool(data_scope.get("companies")) or any(k in topic for k in ["房企", "公司", "年报", "净利润", "华润", "中海", "龙湖", "万科"])

    def _is_city_topic(self, topic: str, data_scope: Dict[str, Any]) -> bool:
        return bool(data_scope.get("cities")) or any(k in topic for k in ["城市", "北京", "上海", "深圳", "杭州", "武汉", "楼市"])

    def _risk_level(self, topic: str, signals: List[Dict[str, Any]], risk_preference: str) -> str:
        if risk_preference == "strict":
            return "high"
        high_risk_words = ["维权", "减配", "质量", "违约", "暴雷", "资金链", "违规", "造假"]
        if any(word in topic for word in high_risk_words):
            return "high"
        if any(item.get("risk") == "high" for item in signals):
            return "high"
        return "medium" if risk_preference == "neutral" else "low"

    def _guardrails(self, article_type: str, risk_level: str) -> List[str]:
        rules = [
            "单篇稿件只保留一个主模型，其他模型只作为事实补充。",
            "所有数据必须标明来源和口径。",
            "模型结论不得直接写成事实结论，需转化为可核验的描述。",
            "避免使用‘整体来看、可以看出、本质上、意味着’等模板表达。",
        ]
        if risk_level == "high":
            rules.extend([
                "涉及企业品质、交付、维权、违规等内容时，只写已核验事实，不作定性。",
                "采访内容需标明是否授权引用，未经核验的说法仅作背景线索。",
                "避免使用‘牺牲品质、恶意、造假、违规’等高风险措辞。",
            ])
        if article_type in ["快讯", "短新闻"]:
            rules.append("不得展开趋势推断或因果链分析。")
        return rules

    def _depth_structure(self, primary: str) -> List[str]:
        mapping = {
            "developer_behavior": ["业绩结果", "利润来源", "行为路径", "待核验影响"],
            "top10_comparison": ["行业分组", "利润来源差异", "行为路径对比", "风险与约束"],
            "trend_evolution": ["微观信号", "传导路径", "质变边界", "后续观察"],
            "city_divergence": ["城市分组", "成交和价格", "土地与政策", "城市样本"],
            "policy_semantic": ["政策原文", "语义变化", "执行对象", "市场反馈"],
            "land_anomaly": ["土地成交变化", "买方结构", "资金链条", "后续消化"],
            "signal_inference": ["异常迹象", "结构拆解", "行为推演", "待核验证据"],
        }
        return mapping.get(primary, ["事实", "结构", "影响", "待核验"])

    def _suppress_except(self, allowed: List[str]) -> List[str]:
        return [model for model in MODEL_REGISTRY if model not in allowed]


def render_orchestration_brief(decision: Dict[str, Any]) -> str:
    """把调度结果渲染为编辑部可读说明。"""
    parts = [
        f"稿件类型：{decision.get('article_type')}",
        f"主模型：{decision.get('primary_model')}",
        f"支撑模型：{'、'.join(decision.get('support_models', []))}",
        f"写作策略：{decision.get('writing_strategy')}",
        f"建议结构：{' / '.join(decision.get('structure_suggestion', []))}",
        f"风险等级：{decision.get('risk_level')}",
    ]
    guardrails = decision.get("guardrails", [])
    if guardrails:
        parts.append("约束：" + "；".join(guardrails))
    return "\n".join(parts)
