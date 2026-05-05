from typing import Any, Dict, List, Optional


YEARLY_REQUIRED_FIELDS = [
    "year",
    "total_land_transaction_amount",
    "city_investment_land_amount",
    "city_investment_amount_share",
    "total_land_gfa",
    "city_investment_land_gfa",
    "city_investment_gfa_share",
]


DISPOSAL_TYPES = [
    "self_development",
    "co_development",
    "entrusted_construction",
    "equity_transfer",
    "land_reserve_repurchase",
    "idle_or_unstarted",
]


SPECIAL_BOND_FIELDS = [
    "special_bond_issued_amount",
    "land_reserve_repurchase_amount",
    "idle_land_repurchase_amount",
    "related_city_investment_land_book_value",
]


def build_city_investment_land_model(data: Dict[str, Any]) -> Dict[str, Any]:
    """构建城投兜底拿地专题模型。

    该模型服务于财经记者的专题研究，不直接假定所有数据完整，
    而是把数据拆成四层：
    1. 年度土地成交和城投拿地规模；
    2. 城投拿地后的消化方式；
    3. 专项债与土地收储/回购之间的资金闭环；
    4. 可转化为报道的选题角度。
    """
    yearly = data.get("yearly", [])
    disposal = data.get("disposal", [])
    special_bonds = data.get("special_bonds", [])

    normalized_yearly = [_normalize_yearly_item(item) for item in yearly]
    yearly_summary = _summarize_yearly_change(normalized_yearly)
    disposal_summary = _summarize_disposal(disposal)
    bond_loop = _analyze_special_bond_loop(special_bonds)
    data_gaps = _detect_data_gaps(normalized_yearly, disposal, special_bonds)
    story_angles = _generate_story_angles(yearly_summary, disposal_summary, bond_loop)
    reporting_framework = _build_reporting_framework()

    return {
        "yearly_summary": yearly_summary,
        "disposal_summary": disposal_summary,
        "special_bond_loop": bond_loop,
        "data_gaps": data_gaps,
        "story_angles": story_angles,
        "reporting_framework": reporting_framework,
        "raw": {
            "yearly": normalized_yearly,
            "disposal": disposal,
            "special_bonds": special_bonds,
        },
    }


def _normalize_yearly_item(item: Dict[str, Any]) -> Dict[str, Any]:
    total_amount = _as_float(item.get("total_land_transaction_amount"))
    city_amount = _as_float(item.get("city_investment_land_amount"))
    amount_share = _as_float(item.get("city_investment_amount_share"))

    if city_amount is None and total_amount is not None and amount_share is not None:
        city_amount = round(total_amount * amount_share / 100, 2)

    if amount_share is None and total_amount and city_amount is not None:
        amount_share = round(city_amount / total_amount * 100, 2)

    total_gfa = _as_float(item.get("total_land_gfa"))
    city_gfa = _as_float(item.get("city_investment_land_gfa"))
    gfa_share = _as_float(item.get("city_investment_gfa_share"))

    if city_gfa is None and total_gfa is not None and gfa_share is not None:
        city_gfa = round(total_gfa * gfa_share / 100, 2)

    if gfa_share is None and total_gfa and city_gfa is not None:
        gfa_share = round(city_gfa / total_gfa * 100, 2)

    return {
        "year": item.get("year"),
        "total_land_transaction_amount": total_amount,
        "city_investment_land_amount": city_amount,
        "city_investment_amount_share": amount_share,
        "total_land_gfa": total_gfa,
        "city_investment_land_gfa": city_gfa,
        "city_investment_gfa_share": gfa_share,
        "scope": item.get("scope", "national_or_sample"),
        "source": item.get("source", "unknown"),
        "note": item.get("note", ""),
    }


def _summarize_yearly_change(yearly: List[Dict[str, Any]]) -> Dict[str, Any]:
    sorted_items = sorted(yearly, key=lambda item: item.get("year") or 0)
    trend_notes = []

    for prev, curr in zip(sorted_items, sorted_items[1:]):
        prev_amount = _as_float(prev.get("city_investment_land_amount"))
        curr_amount = _as_float(curr.get("city_investment_land_amount"))
        if prev_amount and curr_amount is not None:
            yoy = round((curr_amount - prev_amount) / prev_amount * 100, 2)
            trend_notes.append(f"{curr.get('year')}年城投拿地金额同比{yoy}%")

    peak_by_amount = _max_item(sorted_items, "city_investment_land_amount")
    peak_by_share = _max_item(sorted_items, "city_investment_amount_share")

    return {
        "items": sorted_items,
        "trend_notes": trend_notes,
        "peak_by_amount": peak_by_amount,
        "peak_by_share": peak_by_share,
        "interpretation": [
            "2021年以来，城投拿地从局部托底逐步变成土地市场的重要稳定器。",
            "2022年后，房企投资收缩，城投拿地占比明显抬升；2024年部分口径中达到阶段高位。",
            "2025年以后，核心城市土拍改善使城投占比有所回落，但中西部和弱市场城市仍依赖城投托底。",
        ],
    }


def _summarize_disposal(disposal: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary = {key: {"count": 0, "gfa": 0.0, "amount": 0.0} for key in DISPOSAL_TYPES}

    for item in disposal:
        disposal_type = item.get("disposal_type", "idle_or_unstarted")
        if disposal_type not in summary:
            disposal_type = "idle_or_unstarted"
        summary[disposal_type]["count"] += 1
        summary[disposal_type]["gfa"] += _as_float(item.get("gfa")) or 0
        summary[disposal_type]["amount"] += _as_float(item.get("amount")) or 0

    return {
        "summary": summary,
        "interpretation": [
            "城投拿地后的消化路径主要包括自开发、联合开发、委托代建、股权转让、政府收储回购和长期未开工。",
            "如果未开工占比高，说明城投拿地更偏托底属性，而非真实开发投资。",
            "如果代建或合作开发占比提升，说明城投土地正在转化为代建企业和央国企开发商的项目来源。",
            "如果收储回购占比提升，则需要进一步追踪专项债、土地储备和地方财政之间的资金闭环。",
        ],
    }


def _analyze_special_bond_loop(special_bonds: List[Dict[str, Any]]) -> Dict[str, Any]:
    totals = {
        "special_bond_issued_amount": 0.0,
        "land_reserve_repurchase_amount": 0.0,
        "idle_land_repurchase_amount": 0.0,
        "related_city_investment_land_book_value": 0.0,
    }

    for item in special_bonds:
        for field in totals:
            totals[field] += _as_float(item.get(field)) or 0

    loop_ratio = None
    if totals["related_city_investment_land_book_value"]:
        loop_ratio = round(
            totals["land_reserve_repurchase_amount"]
            / totals["related_city_investment_land_book_value"]
            * 100,
            2,
        )

    return {
        "totals": totals,
        "loop_ratio": loop_ratio,
        "logic": [
            "第一步：地方政府通过招拍挂出让土地，城投平台兜底拿地，形成土地出让收入。",
            "第二步：土地出让收入改善政府性基金收入，并可能支撑地方财政和债务安排。",
            "第三步：若地块长期未开发或市场继续下行，政府可通过土地储备专项债或相关专项债资金收购存量闲置土地。",
            "第四步：专项债资金流向土地收储或回购，部分资金可能回到城投或相关国企主体，形成“土地出让—平台拿地—专项债收储/回购”的闭环。",
        ],
        "risk_points": [
            "若专项债收购价格接近原出让价格，需要关注是否实质化解城投资产压力。",
            "若被收储土地来自近年城投托底地块，需要关注是否构成财政资金二次托底。",
            "若收储后再次供地，需要观察土地是否真正进入有效开发，而非循环入库。",
        ],
    }


def _detect_data_gaps(
    yearly: List[Dict[str, Any]],
    disposal: List[Dict[str, Any]],
    special_bonds: List[Dict[str, Any]],
) -> List[str]:
    gaps = []
    for item in yearly:
        missing = [field for field in YEARLY_REQUIRED_FIELDS if item.get(field) is None]
        if missing:
            gaps.append(f"{item.get('year')}年缺少字段：{', '.join(missing)}")

    if not disposal:
        gaps.append("缺少地块级消化状态数据：需补充开工、未开工、合作开发、代建、转让、收储回购等字段。")

    if not special_bonds:
        gaps.append("缺少专项债项目级数据：需补充发行金额、投向、收储地块、原权属主体、收购价格等字段。")

    return gaps


def _generate_story_angles(
    yearly_summary: Dict[str, Any],
    disposal_summary: Dict[str, Any],
    bond_loop: Dict[str, Any],
) -> List[Dict[str, str]]:
    return [
        {
            "title": "城投托底拿地退潮了吗？",
            "angle": "比较2021年以来城投拿地金额、建面和占比变化，区分全国回落与弱市场城市依赖。",
        },
        {
            "title": "城投拿地后的土地去哪了？",
            "angle": "追踪自开发、合作开发、代建、转让、收储和闲置六类消化路径。",
        },
        {
            "title": "专项债是否正在接盘城投手中的土地？",
            "angle": "以专项债募集说明书为依据，追踪收储资金、收购价格和原权属主体。",
        },
        {
            "title": "土地财政的二次循环：从出让收入到专项债收储",
            "angle": "观察土地出让收入、城投资产负债表和专项债资金之间是否形成闭环。",
        },
        {
            "title": "代建企业的新机会与旧风险",
            "angle": "城投未开工土地为代建提供项目池，但项目位置、利润率和付款能力决定真实机会。",
        },
        {
            "title": "谁最依赖城投托底？",
            "angle": "按城市和省份比较城投拿地占比，识别市场化房企退出最明显的区域。",
        },
    ]


def _build_reporting_framework() -> Dict[str, Any]:
    return {
        "lead": "从土地市场收缩与城投托底切入，提出核心问题：城投拿下的土地最终如何消化，是否正在与专项债形成新的资金闭环。",
        "sections": [
            {
                "title": "一、城投托底从阶段现象变成土地市场结构变量",
                "focus": "年度拿地金额、建面、占比及区域分化。",
            },
            {
                "title": "二、开发能力不足下，城投土地的六种消化路径",
                "focus": "自开发、合作开发、代建、转让、收储、闲置。",
            },
            {
                "title": "三、专项债收储打开资金闭环，土地财政逻辑发生变化",
                "focus": "专项债发行规模、收储价格、原权属主体和资金流向。",
            },
            {
                "title": "四、城投托底的隐性成本与后续风险",
                "focus": "资产负债表压力、土地闲置、重复托底、地方财政可持续性。",
            },
        ],
        "interview_targets": [
            "地方自然资源部门人士",
            "城投平台公司人士",
            "专项债承销机构/固收分析师",
            "代建企业项目拓展负责人",
            "地方财政研究人士",
            "土地市场研究机构分析师",
        ],
        "key_questions": [
            "城投拿地是主动投资还是地方托底安排？",
            "拿地资金来源是什么，是否依赖外部融资或政府协调？",
            "城投拿地后开工比例是多少，未开工原因是什么？",
            "是否通过代建、合作开发或股权转让消化土地？",
            "专项债收储地块中有多少来自城投或地方国企？",
            "收储价格与原出让价格之间是否存在明显差异？",
        ],
    }


def _max_item(items: List[Dict[str, Any]], field: str) -> Optional[Dict[str, Any]]:
    valid = [item for item in items if _as_float(item.get(field)) is not None]
    if not valid:
        return None
    return max(valid, key=lambda item: _as_float(item.get(field)) or float("-inf"))


def _as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
