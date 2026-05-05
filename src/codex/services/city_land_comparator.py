from typing import Any, Dict, List, Optional


CITY_METRICS = [
    "total_land_amount",
    "city_investment_land_amount",
    "city_investment_amount_share",
    "total_land_gfa",
    "city_investment_land_gfa",
    "city_investment_gfa_share",
    "private_developer_land_amount",
    "central_soe_land_amount",
    "unsold_rate",
    "premium_rate",
    "failed_auction_rate",
    "started_gfa_share",
    "idle_gfa_share",
    "special_bond_land_reserve_amount",
]


DEPENDENCY_LEVELS = {
    "high": "高度依赖城投托底",
    "medium": "中度依赖城投托底",
    "low": "市场化程度较高",
}


def compare_city_land_markets(cities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """比较不同城市的城投拿地依赖度、市场修复程度和土地消化风险。"""
    normalized = [_normalize_city(city) for city in cities]
    rankings = _build_rankings(normalized)
    city_profiles = [_build_city_profile(city) for city in normalized]
    dependency_groups = _group_by_dependency(city_profiles)
    recovery_groups = _group_by_market_recovery(city_profiles)
    risk_notes = _build_risk_notes(city_profiles)
    storylines = _generate_city_storylines(city_profiles, dependency_groups, recovery_groups)

    return {
        "metrics_compared": CITY_METRICS,
        "rankings": rankings,
        "city_profiles": city_profiles,
        "dependency_groups": dependency_groups,
        "market_recovery_groups": recovery_groups,
        "risk_notes": risk_notes,
        "storylines": storylines,
        "methodology": _methodology(),
    }


def _normalize_city(city: Dict[str, Any]) -> Dict[str, Any]:
    metrics = city.get("metrics", {})

    total_amount = _as_float(metrics.get("total_land_amount"))
    city_amount = _as_float(metrics.get("city_investment_land_amount"))
    amount_share = _as_float(metrics.get("city_investment_amount_share"))
    if amount_share is None and total_amount and city_amount is not None:
        amount_share = round(city_amount / total_amount * 100, 2)
        metrics["city_investment_amount_share"] = amount_share
    if city_amount is None and total_amount is not None and amount_share is not None:
        city_amount = round(total_amount * amount_share / 100, 2)
        metrics["city_investment_land_amount"] = city_amount

    total_gfa = _as_float(metrics.get("total_land_gfa"))
    city_gfa = _as_float(metrics.get("city_investment_land_gfa"))
    gfa_share = _as_float(metrics.get("city_investment_gfa_share"))
    if gfa_share is None and total_gfa and city_gfa is not None:
        gfa_share = round(city_gfa / total_gfa * 100, 2)
        metrics["city_investment_gfa_share"] = gfa_share
    if city_gfa is None and total_gfa is not None and gfa_share is not None:
        city_gfa = round(total_gfa * gfa_share / 100, 2)
        metrics["city_investment_land_gfa"] = city_gfa

    return {
        "city": city.get("city", "未知城市"),
        "province": city.get("province", "未知省份"),
        "year": city.get("year", "未知年份"),
        "tier": city.get("tier", "unknown"),
        "metrics": metrics,
        "source": city.get("source", "unknown"),
        "note": city.get("note", ""),
    }


def _build_city_profile(city: Dict[str, Any]) -> Dict[str, Any]:
    metrics = city["metrics"]
    amount_share = _as_float(metrics.get("city_investment_amount_share"))
    gfa_share = _as_float(metrics.get("city_investment_gfa_share"))
    premium_rate = _as_float(metrics.get("premium_rate"))
    failed_auction_rate = _as_float(metrics.get("failed_auction_rate"))
    started_gfa_share = _as_float(metrics.get("started_gfa_share"))
    idle_gfa_share = _as_float(metrics.get("idle_gfa_share"))
    special_bond_amount = _as_float(metrics.get("special_bond_land_reserve_amount"))
    private_amount = _as_float(metrics.get("private_developer_land_amount"))
    central_soe_amount = _as_float(metrics.get("central_soe_land_amount"))

    dependency_score = _score_dependency(amount_share, gfa_share)
    recovery_score = _score_market_recovery(
        amount_share=amount_share,
        premium_rate=premium_rate,
        failed_auction_rate=failed_auction_rate,
        private_amount=private_amount,
        central_soe_amount=central_soe_amount,
    )
    disposal_risk = _score_disposal_risk(started_gfa_share, idle_gfa_share)
    bond_loop_risk = _score_bond_loop_risk(special_bond_amount, metrics.get("city_investment_land_amount"))

    dependency_level = _dependency_level(dependency_score)
    recovery_level = _recovery_level(recovery_score)

    return {
        "city": city["city"],
        "province": city["province"],
        "year": city["year"],
        "tier": city["tier"],
        "metrics": metrics,
        "dependency_score": dependency_score,
        "dependency_level": dependency_level,
        "market_recovery_score": recovery_score,
        "market_recovery_level": recovery_level,
        "disposal_risk_score": disposal_risk,
        "bond_loop_risk_score": bond_loop_risk,
        "diagnosis": _diagnose_city(
            city=city,
            dependency_level=dependency_level,
            recovery_level=recovery_level,
            disposal_risk=disposal_risk,
            bond_loop_risk=bond_loop_risk,
        ),
    }


def _build_rankings(cities: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    rankings: Dict[str, List[Dict[str, Any]]] = {}
    for metric in CITY_METRICS:
        rows = []
        for city in cities:
            value = _as_float(city["metrics"].get(metric))
            if value is not None:
                rows.append({"city": city["city"], "value": value})
        rankings[metric] = sorted(rows, key=lambda item: item["value"], reverse=True)
    return rankings


def _score_dependency(amount_share: Optional[float], gfa_share: Optional[float]) -> float:
    shares = [share for share in [amount_share, gfa_share] if share is not None]
    if not shares:
        return 0.0
    avg_share = sum(shares) / len(shares)
    return round(min(avg_share, 100), 2)


def _score_market_recovery(
    amount_share: Optional[float],
    premium_rate: Optional[float],
    failed_auction_rate: Optional[float],
    private_amount: Optional[float],
    central_soe_amount: Optional[float],
) -> float:
    score = 50.0

    if amount_share is not None:
        score -= min(amount_share * 0.5, 40)
    if premium_rate is not None:
        score += min(premium_rate * 1.5, 25)
    if failed_auction_rate is not None:
        score -= min(failed_auction_rate * 0.8, 25)
    if private_amount is not None and private_amount > 0:
        score += 10
    if central_soe_amount is not None and central_soe_amount > 0:
        score += 5

    return round(max(min(score, 100), 0), 2)


def _score_disposal_risk(started_gfa_share: Optional[float], idle_gfa_share: Optional[float]) -> float:
    score = 50.0
    if started_gfa_share is not None:
        score -= min(started_gfa_share * 0.5, 35)
    if idle_gfa_share is not None:
        score += min(idle_gfa_share * 0.8, 40)
    return round(max(min(score, 100), 0), 2)


def _score_bond_loop_risk(special_bond_amount: Optional[float], city_investment_amount: Any) -> float:
    city_amount = _as_float(city_investment_amount)
    if special_bond_amount is None or city_amount is None or city_amount == 0:
        return 0.0
    return round(min(special_bond_amount / city_amount * 100, 100), 2)


def _dependency_level(score: float) -> str:
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def _recovery_level(score: float) -> str:
    if score >= 65:
        return "market_recovering"
    if score >= 40:
        return "weak_recovery"
    return "policy_supported"


def _diagnose_city(
    city: Dict[str, Any],
    dependency_level: str,
    recovery_level: str,
    disposal_risk: float,
    bond_loop_risk: float,
) -> List[str]:
    metrics = city["metrics"]
    diagnosis = []

    if dependency_level == "high":
        diagnosis.append("城投拿地占比较高，土地市场仍主要依赖地方平台托底。")
    elif dependency_level == "medium":
        diagnosis.append("城投仍是重要买方，但市场化房企或央国企已有一定参与。")
    else:
        diagnosis.append("城投依赖度较低，土地市场化程度相对更高。")

    if recovery_level == "market_recovering":
        diagnosis.append("溢价率、民企或央国企参与度显示市场化修复迹象。")
    elif recovery_level == "weak_recovery":
        diagnosis.append("土地市场边际修复但仍不稳定，城投托底与市场化拿地并存。")
    else:
        diagnosis.append("土地市场修复较弱，更依赖政策托底和平台拿地。")

    if disposal_risk >= 60:
        diagnosis.append("土地消化风险偏高，需要重点核查开工率、闲置率、代建和收储路径。")

    if bond_loop_risk >= 30:
        diagnosis.append("专项债收储与城投拿地可能存在较强关联，需要追踪资金是否形成闭环。")

    if _as_float(metrics.get("failed_auction_rate")) and _as_float(metrics.get("failed_auction_rate")) >= 20:
        diagnosis.append("流拍率较高，说明真实市场买方不足。")

    return diagnosis


def _group_by_dependency(city_profiles: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    groups = {"high": [], "medium": [], "low": []}
    for profile in city_profiles:
        groups[profile["dependency_level"]].append(profile["city"])
    return groups


def _group_by_market_recovery(city_profiles: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    groups = {"market_recovering": [], "weak_recovery": [], "policy_supported": []}
    for profile in city_profiles:
        groups[profile["market_recovery_level"]].append(profile["city"])
    return groups


def _build_risk_notes(city_profiles: List[Dict[str, Any]]) -> List[str]:
    notes = []
    high_dependency = [p["city"] for p in city_profiles if p["dependency_level"] == "high"]
    high_disposal = [p["city"] for p in city_profiles if p["disposal_risk_score"] >= 60]
    high_bond = [p["city"] for p in city_profiles if p["bond_loop_risk_score"] >= 30]

    if high_dependency:
        notes.append("城投依赖度较高城市：" + "、".join(high_dependency))
    if high_disposal:
        notes.append("土地消化风险较高城市：" + "、".join(high_disposal))
    if high_bond:
        notes.append("专项债闭环风险较高城市：" + "、".join(high_bond))
    if not notes:
        notes.append("当前样本未触发高风险提示，但仍需补充地块级和专项债项目级数据。")
    return notes


def _generate_city_storylines(
    city_profiles: List[Dict[str, Any]],
    dependency_groups: Dict[str, List[str]],
    recovery_groups: Dict[str, List[str]],
) -> List[Dict[str, Any]]:
    return [
        {
            "title": "哪些城市仍依赖城投托底拿地",
            "angle": "按城投拿地金额占比和建面占比分组，识别市场化房企退出更明显的城市。",
            "cities": dependency_groups["high"],
            "core_question": "城投高占比是短期托底，还是地方土地市场长期结构变化？",
        },
        {
            "title": "哪些城市土地市场已恢复市场化买方",
            "angle": "以溢价率、流拍率、民企和央国企参与度衡量土地市场真实修复。",
            "cities": recovery_groups["market_recovering"],
            "core_question": "市场化恢复来自核心地块供应，还是城市基本面改善？",
        },
        {
            "title": "城投拿地后的消化风险地图",
            "angle": "比较城市开工率、闲置率、代建比例和收储规模，判断城投土地是否真正进入开发。",
            "cities": [profile["city"] for profile in city_profiles],
            "core_question": "哪些城市只是把土地从财政表转移到了城投资产负债表？",
        },
        {
            "title": "专项债收储是否正在重塑地方土地财政循环",
            "angle": "把专项债收储金额与城投拿地规模挂钩，观察资金是否回流平台公司。",
            "cities": [profile["city"] for profile in city_profiles],
            "core_question": "专项债是盘活存量土地，还是二次接盘城投托底地块？",
        },
    ]


def _methodology() -> Dict[str, Any]:
    return {
        "dependency_score": "城投拿地金额占比和建面占比的均值，越高表示越依赖城投托底。",
        "market_recovery_score": "综合城投占比、溢价率、流拍率、民企和央国企参与度，越高表示市场化恢复越强。",
        "disposal_risk_score": "综合开工比例和闲置比例，越高表示城投拿地后消化压力越大。",
        "bond_loop_risk_score": "专项债土地收储金额/城投拿地金额，越高表示专项债与城投土地可能存在更强资金闭环。",
        "data_requirements": [
            "自然资源部门土地成交公告",
            "中指/CRIC/Wind土地成交数据库",
            "城投公司债券募集说明书",
            "专项债发行募集说明书",
            "地块开工、施工、竣工和权属变更信息",
        ],
    }


def _as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
