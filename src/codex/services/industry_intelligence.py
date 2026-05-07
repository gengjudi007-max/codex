from __future__ import annotations

from typing import Any, Dict, List

from codex.services.policy_semantics import analyze_policy_semantics
from codex.services.risk_chain import analyze_risk_chain
from codex.services.text_utils import infer_city, infer_company, normalize_text, unique

CITY_CYCLE_SIGNALS = {
    "recovery": ["溢价率回升", "民企回归", "成交回升", "去化改善", "二手房成交增加"],
    "pressure": ["流拍", "底价成交", "库存", "去化压力", "价格下跌", "成交低迷"],
    "government_support": ["城投拿地", "地方平台", "托底", "专项债", "收储", "保障房"],
}

DEVELOPER_STRATEGY_SIGNALS = {
    "defensive": ["收缩", "降负债", "现金流", "减值", "谨慎拿地", "退出"],
    "selective_growth": ["核心城市", "改善型", "高能级", "聚焦", "补仓"],
    "distress": ["债务重组", "展期", "违约", "亏损", "流动性压力"],
}

PROPERTY_SERVICE_SIGNALS = {
    "scale_expansion_aftershock": ["在管面积", "合同面积", "收并购", "规模扩张"],
    "quality_contraction": ["撤场", "退出低效项目", "不再续约", "项目优化"],
    "cash_pressure": ["应收账款", "毛利率", "增值服务", "关联方"],
}

LAND_FINANCE_SIGNALS = {
    "land_revenue_pressure": ["土地财政", "土地出让收入", "流拍", "底价成交"],
    "city_investment_support": ["城投拿地", "地方平台", "托底"],
    "inventory_policy": ["收储", "专项债", "保障房", "合理控制新增房地产用地供应"],
}


def analyze_industry_intelligence(payload: Dict[str, Any]) -> Dict[str, Any]:
    text = _payload_text(payload)
    city = payload.get("city") or infer_city(text)
    company = payload.get("company") or infer_company(text)

    city_cycle = _match_dimension(text, CITY_CYCLE_SIGNALS)
    developer_strategy = _match_dimension(text, DEVELOPER_STRATEGY_SIGNALS)
    property_cycle = _match_dimension(text, PROPERTY_SERVICE_SIGNALS)
    land_finance = _match_dimension(text, LAND_FINANCE_SIGNALS)
    risk = analyze_risk_chain(payload)
    policy = analyze_policy_semantics(
        payload.get("current_policy") or payload.get("current") or text,
        payload.get("previous_policy") or payload.get("previous") or "",
    )

    return {
        "city": city,
        "company": company,
        "city_cycle": city_cycle,
        "developer_strategy": developer_strategy,
        "property_service_cycle": property_cycle,
        "land_finance": land_finance,
        "risk_chain": risk,
        "policy_semantics": policy,
        "industry_reading": _industry_reading(city_cycle, developer_strategy, property_cycle, land_finance),
        "reporting_implications": _reporting_implications(city_cycle, developer_strategy, property_cycle, land_finance),
        "claim_boundary": "行业认知层基于规则和文本信号生成分析框架，不能替代市场数据、财务数据和采访核验。",
    }


def _payload_text(payload: Dict[str, Any]) -> str:
    parts: List[str] = []
    for key in ("title", "summary", "content", "text", "message", "current_policy", "previous_policy"):
        parts.append(str(payload.get(key, "")))
    if isinstance(payload.get("items"), list):
        for item in payload["items"]:
            if isinstance(item, dict):
                parts.extend(str(item.get(key, "")) for key in ("title", "summary", "content", "text"))
    return normalize_text(" ".join(parts))


def _match_dimension(text: str, rules: Dict[str, List[str]]) -> Dict[str, Any]:
    matches = []
    for name, keywords in rules.items():
        hits = [keyword for keyword in keywords if keyword in text]
        if hits:
            matches.append({"signal": name, "keywords": unique(hits), "score": min(len(hits) * 25, 100)})
    return {
        "signals": sorted(matches, key=lambda item: item["score"], reverse=True),
        "dominant_signal": matches[0]["signal"] if matches else "unknown",
    }


def _industry_reading(
    city_cycle: Dict[str, Any],
    developer_strategy: Dict[str, Any],
    property_cycle: Dict[str, Any],
    land_finance: Dict[str, Any],
) -> List[str]:
    readings = []
    if city_cycle.get("dominant_signal") == "government_support":
        readings.append("城市市场可能仍依赖政府或平台力量托底，需区分真实需求修复与行政性支撑。")
    if city_cycle.get("dominant_signal") == "pressure":
        readings.append("城市成交、价格或库存压力仍是报道主线，应继续追踪去化和土地供应变化。")
    if developer_strategy.get("dominant_signal") == "defensive":
        readings.append("房企策略更偏防守，现金流、安全边际和投资收缩应成为分析重点。")
    if developer_strategy.get("dominant_signal") == "distress":
        readings.append("企业可能处于风险处置阶段，债务期限、资产减值和项目交付需优先核验。")
    if property_cycle.get("dominant_signal") == "quality_contraction":
        readings.append("物业企业可能从规模扩张转向质量经营，退出低效项目背后是利润率和现金流再平衡。")
    if land_finance.get("dominant_signal") == "inventory_policy":
        readings.append("土地和库存政策正在影响地方财政、供地节奏和收储资金安排。")
    return readings or ["暂未形成明确行业判断，需要补充数据、政策文件或采访材料。"]


def _reporting_implications(
    city_cycle: Dict[str, Any],
    developer_strategy: Dict[str, Any],
    property_cycle: Dict[str, Any],
    land_finance: Dict[str, Any],
) -> List[str]:
    implications = [
        "优先补充权威数据和一手文件，避免仅依据市场传闻下判断。",
        "把企业动作放入城市周期、融资环境和政策约束中分析。",
    ]
    if land_finance.get("signals"):
        implications.append("土地财政相关选题应追踪城投拿地、专项债、收储和地块后续开发状态。")
    if property_cycle.get("signals"):
        implications.append("物业服务选题应同时看在管面积、合同面积、应收账款和项目退出。")
    if developer_strategy.get("signals"):
        implications.append("房企选题应拆分利润表、现金流、减值和债务结构。")
    if city_cycle.get("signals"):
        implications.append("城市市场选题应区分成交修复、价格修复和政府托底。")
    return implications
