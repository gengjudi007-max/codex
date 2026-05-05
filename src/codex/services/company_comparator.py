from typing import Any, Dict, List, Optional


CORE_METRICS = [
    "revenue",
    "revenue_yoy",
    "net_profit",
    "net_profit_yoy",
    "land_acquisition_amount",
    "land_acquisition_gfa",
    "sales_amount",
    "sales_amount_yoy",
    "sales_area",
    "sales_area_yoy",
]


def compare_developers(companies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """横向比较开发型房企经营表现。

    输入建议：
    {
        "company": "保利发展",
        "year": 2025,
        "metrics": {
            "revenue": 3000,
            "revenue_yoy": -10,
            "net_profit": 120,
            "net_profit_yoy": 20,
            "gross_margin": 18,
            "impairment_loss": 30,
            "land_acquisition_amount": 500,
            "land_acquisition_gfa": 600,
            "sales_amount": 3200,
            "sales_amount_yoy": -15,
            "sales_area": 1800,
            "sales_area_yoy": -12,
            "inventory_pressure": "medium",
            "city_exposure": "core_city",
            "debt_pressure": "low",
        }
    }
    """
    normalized = [_normalize_company(company) for company in companies]
    rankings = _build_rankings(normalized)
    profit_groups = _group_by_profit_performance(normalized)
    divergence = _analyze_profit_divergence(normalized)
    development_logic = _analyze_development_business_logic(normalized)
    storylines = _generate_storylines(normalized, profit_groups, divergence)

    return {
        "metrics_compared": CORE_METRICS,
        "rankings": rankings,
        "profit_groups": profit_groups,
        "profit_divergence_analysis": divergence,
        "development_business_analysis": development_logic,
        "storylines": storylines,
        "companies": normalized,
    }


def _normalize_company(company: Dict[str, Any]) -> Dict[str, Any]:
    metrics = company.get("metrics", {})
    return {
        "company": company.get("company", "未知房企"),
        "year": company.get("year", "未知年份"),
        "metrics": metrics,
        "diagnosis": _diagnose_company(metrics),
    }


def _build_rankings(companies: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    rankings: Dict[str, List[Dict[str, Any]]] = {}
    for metric in CORE_METRICS:
        ranked = []
        for company in companies:
            value = _as_float(company["metrics"].get(metric))
            if value is not None:
                ranked.append({"company": company["company"], "value": value})
        rankings[metric] = sorted(ranked, key=lambda item: item["value"], reverse=True)
    return rankings


def _group_by_profit_performance(companies: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    groups = {
        "profit_surge": [],
        "profit_stable": [],
        "profit_decline": [],
        "loss_making": [],
    }
    for company in companies:
        metrics = company["metrics"]
        net_profit = _as_float(metrics.get("net_profit"))
        net_profit_yoy = _as_float(metrics.get("net_profit_yoy"))

        if net_profit is not None and net_profit < 0:
            groups["loss_making"].append(company["company"])
        elif net_profit_yoy is not None and net_profit_yoy >= 30:
            groups["profit_surge"].append(company["company"])
        elif net_profit_yoy is not None and net_profit_yoy <= -30:
            groups["profit_decline"].append(company["company"])
        else:
            groups["profit_stable"].append(company["company"])
    return groups


def _diagnose_company(metrics: Dict[str, Any]) -> List[str]:
    diagnosis = []

    gross_margin = _as_float(metrics.get("gross_margin"))
    impairment_loss = _as_float(metrics.get("impairment_loss"))
    sales_amount_yoy = _as_float(metrics.get("sales_amount_yoy"))
    land_acquisition_amount = _as_float(metrics.get("land_acquisition_amount"))
    debt_pressure = metrics.get("debt_pressure")
    city_exposure = metrics.get("city_exposure")
    inventory_pressure = metrics.get("inventory_pressure")

    if gross_margin is not None and gross_margin >= 20:
        diagnosis.append("毛利率相对较高，说明结算项目质量、土地成本或产品结构较好")
    elif gross_margin is not None and gross_margin < 15:
        diagnosis.append("毛利率偏低，可能受高价地结转、降价销售或低毛利项目集中交付影响")

    if impairment_loss is not None and impairment_loss >= 30:
        diagnosis.append("减值规模较大，对当期利润形成明显侵蚀")
    elif impairment_loss is not None and impairment_loss < 10:
        diagnosis.append("减值压力相对可控，利润表受历史包袱影响较小")

    if sales_amount_yoy is not None and sales_amount_yoy <= -25:
        diagnosis.append("销售金额明显下滑，后续收入结转和现金流承压")
    elif sales_amount_yoy is not None and sales_amount_yoy >= 0:
        diagnosis.append("销售保持韧性，说明城市布局、产品适配或去化能力较强")

    if land_acquisition_amount is not None and land_acquisition_amount > 0:
        diagnosis.append("仍保持一定拿地强度，反映其对后续规模和核心城市补仓仍有诉求")
    else:
        diagnosis.append("拿地趋于谨慎，可能进入现金流优先和库存去化阶段")

    if debt_pressure == "high":
        diagnosis.append("债务压力较高，融资成本和流动性约束可能压制经营修复")
    elif debt_pressure == "low":
        diagnosis.append("债务压力较低，财务安全垫有助于穿越周期")

    if city_exposure == "core_city":
        diagnosis.append("布局更多集中在核心城市，销售去化和资产保值能力相对更强")
    elif city_exposure == "low_tier_city":
        diagnosis.append("低能级城市敞口较高，可能面临更大库存和价格调整压力")

    if inventory_pressure == "high":
        diagnosis.append("库存压力较高，可能带来降价促销、减值和现金回笼压力")

    return diagnosis


def _analyze_profit_divergence(companies: List[Dict[str, Any]]) -> List[str]:
    analysis = []
    profit_surge = []
    profit_decline_or_loss = []

    for company in companies:
        metrics = company["metrics"]
        net_profit = _as_float(metrics.get("net_profit"))
        net_profit_yoy = _as_float(metrics.get("net_profit_yoy"))
        if net_profit_yoy is not None and net_profit_yoy >= 30:
            profit_surge.append(company)
        if (net_profit_yoy is not None and net_profit_yoy <= -30) or (net_profit is not None and net_profit < 0):
            profit_decline_or_loss.append(company)

    if profit_surge:
        names = "、".join(company["company"] for company in profit_surge)
        analysis.append(f"{names}净利润增幅较高，通常需要重点核验是否来自结算毛利改善、减值减少、投资收益或非经常性收益。")

    if profit_decline_or_loss:
        names = "、".join(company["company"] for company in profit_decline_or_loss)
        analysis.append(f"{names}利润大幅下滑或亏损，需拆分销售下滑、毛利率下行、资产减值、融资成本和历史高价地包袱。")

    analysis.append("在同样的外部环境中，利润分化的核心不只在市场冷热，而在土地成本、城市布局、产品去化、减值节奏、债务结构和结算周期的差异。")
    analysis.append("净利润大增并不必然代表主业强修复，需要区分经营性改善与一次性收益；亏损也不一定只是销售差，可能是集中减值和历史项目结转造成。")
    return analysis


def _analyze_development_business_logic(companies: List[Dict[str, Any]]) -> List[str]:
    return [
        "同样以开发业务为主，利润高低首先取决于结转项目的土地成本和售价差。高价地集中结转的企业，即便销售规模不低，也可能出现低毛利甚至亏损。",
        "城市布局决定去化质量。核心城市项目通常抗跌性更强，低能级城市项目在下行期更容易遭遇降价、库存和减值压力。",
        "财务结构影响利润韧性。债务压力高的企业需要承担更高融资成本，也更可能通过降价回款牺牲利润。",
        "拿地节奏决定后续周期位置。前期激进扩张的企业可能在市场下行期承受高价地和库存包袱；谨慎补仓的企业短期规模可能下降，但利润质量更稳。",
        "利润表现还要区分会计利润与经营现金流。部分企业利润改善可能来自投资收益、减值减少或费用压降，但若销售和现金流未同步修复，持续性仍需观察。",
    ]


def _generate_storylines(
    companies: List[Dict[str, Any]],
    profit_groups: Dict[str, List[str]],
    divergence: List[str],
) -> List[Dict[str, Any]]:
    storylines = []

    if profit_groups["profit_surge"] and (profit_groups["profit_decline"] or profit_groups["loss_making"]):
        storylines.append({
            "title": "同一周期下的利润分化：为什么有的房企净利大增，有的仍在亏损",
            "angle": "以净利润同比变化为切口，拆解毛利率、减值、土地成本、城市布局和债务结构差异。",
            "companies": profit_groups["profit_surge"] + profit_groups["profit_decline"] + profit_groups["loss_making"],
            "core_question": "利润修复是经营改善，还是会计因素和低基数效应？",
        })

    storylines.append({
        "title": "开发主业的真实质量：销售规模之外，房企利润由什么决定",
        "angle": "比较销售金额、销售面积、拿地强度与利润表现之间的错位，寻找规模与盈利脱钩的原因。",
        "companies": [company["company"] for company in companies],
        "core_question": "销售规模大是否仍然意味着利润能力强？",
    })

    storylines.append({
        "title": "拿地分化背后的周期判断：谁在补仓，谁在收缩",
        "angle": "从拿地金额和拿地建筑面积观察企业对后市的判断、财务安全边界和城市布局取舍。",
        "companies": [company["company"] for company in companies],
        "core_question": "当前拿地是逆周期补仓，还是被迫维持规模？",
    })

    return storylines


def _as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
