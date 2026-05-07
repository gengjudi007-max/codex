from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


BEHAVIOR_TYPES = [
    "运营补开发",
    "开发挤利润",
    "收缩保现金",
    "激进降价去化",
    "资产处置补利润",
    "高周转续命",
    "稳健均衡型",
    "风险暴露型",
]


@dataclass
class DeveloperBehaviorResult:
    company: str
    behavior_type: str
    confidence: float
    structure_analysis: Dict[str, Any]
    key_actions: List[str]
    consequence_chain: List[str]
    trend_judgement: str
    reporting_angle: str
    verification_gaps: List[str]


class DeveloperBehaviorEngine:
    """房企行为识别引擎。

    目标：
    - 从财报、销售、拿地、经营性业务、现金流、交付和舆情等信号中识别房企行为路径；
    - 区分“利润结果”和“利润质量”；
    - 输出可用于深度报道的行为链条和后续约束。
    """

    def analyze(self, company_data: Dict[str, Any], market_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        market_context = market_context or {}
        company = company_data.get("company", "未知房企")
        structure = self._structure_analysis(company_data)
        behavior_type = self._classify_behavior(company_data, structure, market_context)
        confidence = self._confidence(company_data, structure)
        key_actions = self._key_actions(company_data, behavior_type)
        consequence_chain = self._consequence_chain(company_data, behavior_type)
        trend_judgement = self._trend_judgement(company_data, behavior_type, structure)
        reporting_angle = self._reporting_angle(company, behavior_type, trend_judgement)
        gaps = self._verification_gaps(company_data)

        return asdict(
            DeveloperBehaviorResult(
                company=company,
                behavior_type=behavior_type,
                confidence=confidence,
                structure_analysis=structure,
                key_actions=key_actions,
                consequence_chain=consequence_chain,
                trend_judgement=trend_judgement,
                reporting_angle=reporting_angle,
                verification_gaps=gaps,
            )
        )

    def _structure_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        revenue = _num(data.get("revenue"))
        net_profit = _num(data.get("net_profit"))
        development_profit = _num(data.get("development_profit"))
        operation_profit = _num(data.get("operation_profit"))
        operation_revenue = _num(data.get("operation_revenue"))
        impairment = _num(data.get("impairment"))
        operating_cashflow = _num(data.get("operating_cashflow"))

        operation_profit_cover = None
        if net_profit and operation_profit is not None:
            operation_profit_cover = round(operation_profit / abs(net_profit), 4)

        operation_revenue_share = None
        if revenue and operation_revenue is not None:
            operation_revenue_share = round(operation_revenue / revenue, 4)

        development_profit_share = None
        if net_profit and development_profit is not None:
            development_profit_share = round(development_profit / abs(net_profit), 4)

        return {
            "revenue": revenue,
            "net_profit": net_profit,
            "development_profit": development_profit,
            "operation_profit": operation_profit,
            "operation_profit_cover": operation_profit_cover,
            "operation_revenue_share": operation_revenue_share,
            "development_profit_share": development_profit_share,
            "impairment": impairment,
            "operating_cashflow": operating_cashflow,
            "profit_source": self._profit_source(development_profit_share, operation_profit_cover),
        }

    def _profit_source(self, development_profit_share: Optional[float], operation_profit_cover: Optional[float]) -> str:
        if operation_profit_cover is not None and operation_profit_cover >= 0.5:
            return "运营利润支撑较强"
        if development_profit_share is not None and development_profit_share >= 0.7:
            return "开发利润依赖较高"
        if operation_profit_cover is not None and operation_profit_cover >= 0.25:
            return "运营利润形成一定补充"
        return "利润来源仍需进一步拆解"

    def _classify_behavior(self, data: Dict[str, Any], structure: Dict[str, Any], market_context: Dict[str, Any]) -> str:
        net_profit_yoy = _num(data.get("net_profit_yoy"))
        gross_margin = _num(data.get("gross_margin"))
        sales_yoy = _num(data.get("sales_yoy"))
        land_amount_yoy = _num(data.get("land_amount_yoy"))
        quality_disputes = _num(data.get("quality_disputes")) or 0
        discount_signal = bool(data.get("discount_signal"))
        asset_disposal_gain = _num(data.get("asset_disposal_gain")) or 0
        operating_cashflow = structure.get("operating_cashflow")

        if structure.get("operation_profit_cover") is not None and structure["operation_profit_cover"] >= 0.45:
            return "运营补开发"
        if asset_disposal_gain > 0 and structure.get("net_profit") and asset_disposal_gain / abs(structure["net_profit"]) >= 0.25:
            return "资产处置补利润"
        if quality_disputes > 0 and structure.get("profit_source") == "开发利润依赖较高":
            return "开发挤利润"
        if operating_cashflow is not None and operating_cashflow < 0 and sales_yoy is not None and sales_yoy < -20:
            return "收缩保现金"
        if discount_signal and sales_yoy is not None and sales_yoy < 0:
            return "激进降价去化"
        if land_amount_yoy is not None and land_amount_yoy > 30 and sales_yoy is not None and sales_yoy < 0:
            return "高周转续命"
        if net_profit_yoy is not None and net_profit_yoy < -50:
            return "风险暴露型"
        return "稳健均衡型"

    def _confidence(self, data: Dict[str, Any], structure: Dict[str, Any]) -> float:
        fields = [
            "revenue",
            "net_profit",
            "development_profit",
            "operation_profit",
            "sales_amount",
            "land_amount",
            "operating_cashflow",
            "gross_margin",
        ]
        filled = sum(1 for field in fields if data.get(field) is not None)
        verified = 1 if data.get("verified") else 0
        return round(min(0.25 + filled * 0.08 + verified * 0.15, 1.0), 2)

    def _key_actions(self, data: Dict[str, Any], behavior_type: str) -> List[str]:
        mapping = {
            "运营补开发": ["提高经营性业务贡献", "以商业、物业或租赁业务对冲开发波动", "控制开发投资节奏"],
            "开发挤利润": ["强化开发端利润率", "压缩成本或费用", "提高项目利润贡献"],
            "收缩保现金": ["减少拿地", "压缩开支", "加快回款", "控制债务"],
            "激进降价去化": ["加大折扣", "提高渠道依赖", "加快库存去化"],
            "资产处置补利润": ["出售资产", "确认投资收益", "补充当期利润"],
            "高周转续命": ["继续补仓", "提高周转速度", "用新增项目维持规模"],
            "风险暴露型": ["减值计提", "项目调整", "债务重组或资产收缩"],
            "稳健均衡型": ["保持投资节奏", "控制杠杆", "维持多元业务平衡"],
        }
        return mapping.get(behavior_type, [])

    def _consequence_chain(self, data: Dict[str, Any], behavior_type: str) -> List[str]:
        mapping = {
            "运营补开发": ["开发业务下行", "经营性业务贡献提升", "利润波动被部分对冲", "利润结构稳定性增强"],
            "开发挤利润": ["开发业务承压", "利润率压力上升", "成本控制强化", "交付品质和客户体验承压", "维权或口碑风险增加", "在售项目去化受影响"],
            "收缩保现金": ["销售下行", "现金流压力增加", "投资收缩", "规模下降", "短期安全性提升", "长期增长动能减弱"],
            "激进降价去化": ["库存压力上升", "折扣扩大", "成交阶段性改善", "价格预期承压", "利润率下降"],
            "资产处置补利润": ["主营利润承压", "出售资产补充收益", "当期利润改善", "可持续性取决于资产储备"],
            "高周转续命": ["销售承压", "继续补仓", "资金占用增加", "去化不确定性提高"],
            "风险暴露型": ["销售下降", "利润下滑", "减值增加", "债务和交付压力上升"],
            "稳健均衡型": ["多项指标波动有限", "业务结构相对均衡", "需继续观察行业下行传导"],
        }
        return mapping.get(behavior_type, [])

    def _trend_judgement(self, data: Dict[str, Any], behavior_type: str, structure: Dict[str, Any]) -> str:
        if behavior_type == "运营补开发":
            return "利润结构相对多元，经营性业务对开发波动形成补充。"
        if behavior_type == "开发挤利润":
            return "利润对开发端依赖较高，若项目品质、口碑或去化承压，后续利润持续性需继续核验。"
        if behavior_type == "收缩保现金":
            return "短期现金安全优先于规模增长，后续关注销售回款和投资恢复节奏。"
        if behavior_type == "激进降价去化":
            return "成交改善可能伴随价格和利润率压力，需关注降价是否影响后续预期。"
        if behavior_type == "资产处置补利润":
            return "当期利润受非经常性或资产处置因素影响，主营盈利能力需单独拆解。"
        if behavior_type == "风险暴露型":
            return "利润和现金流压力已经显现，需继续核验债务、交付和项目去化。"
        return "企业表现相对均衡，仍需结合行业下行和区域市场变化持续观察。"

    def _reporting_angle(self, company: str, behavior_type: str, trend: str) -> str:
        return f"{company}可按“{behavior_type}”路径拆解：先写利润来源，再写企业行为，最后写该路径对后续销售、交付和品牌的影响。{trend}"

    def _verification_gaps(self, data: Dict[str, Any]) -> List[str]:
        gaps = []
        required = ["revenue", "net_profit", "sales_amount", "gross_margin", "operating_cashflow"]
        for field in required:
            if data.get(field) is None:
                gaps.append(f"缺少{field}数据")
        if data.get("quality_disputes") and not data.get("quality_disputes_verified"):
            gaps.append("交付品质或维权相关信息需核验，避免直接定性")
        if not data.get("source"):
            gaps.append("缺少数据来源")
        return gaps


def render_developer_behavior_for_article(result: Dict[str, Any]) -> str:
    company = result.get("company")
    behavior_type = result.get("behavior_type")
    structure = result.get("structure_analysis", {})
    chain = result.get("consequence_chain", [])
    trend = result.get("trend_judgement")

    paragraphs = [
        f"{company}被归入“{behavior_type}”路径。其利润结构显示，{structure.get('profit_source', '利润来源仍需进一步拆解')}。",
        f"这一类路径通常表现为：{' → '.join(chain)}。",
        trend or "后续仍需结合销售、现金流和项目表现继续核验。",
    ]
    return "\n\n".join(paragraphs)


def _num(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
