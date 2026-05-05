from __future__ import annotations

from typing import Dict, Optional


CITY_INVESTMENT_KEYWORDS = [
    "城投",
    "城市投资",
    "城市建设",
    "城市发展",
    "城建",
    "城发",
    "城开",
    "城更",
    "城建集团",
    "基础设施投资",
    "建设投资",
    "交通投资",
    "轨道交通",
    "地铁",
    "开发投资",
    "国有资本运营",
]

CENTRAL_SOE_KEYWORDS = [
    "中海",
    "华润",
    "保利",
    "招商",
    "中国铁建",
    "中国中铁",
    "中交",
    "中建",
    "中国金茂",
    "中粮",
    "电建",
]

LOCAL_SOE_KEYWORDS = [
    "国资",
    "国投",
    "国控",
    "国有",
    "国盛",
    "国贸",
    "国开",
    "国企",
]

PRIVATE_DEVELOPER_KEYWORDS = [
    "龙湖",
    "滨江",
    "绿城",
    "万科",
    "新希望",
    "伟星",
    "建发房产",
    "美的置业",
]


def classify_company_ownership(name: Optional[str]) -> Dict[str, object]:
    text = (name or "").strip()
    if not text:
        return {"ownership": "unknown", "confidence": 0.0, "matched_keyword": None}

    for keyword in CITY_INVESTMENT_KEYWORDS:
        if keyword in text:
            return {"ownership": "city_investment", "confidence": 0.9, "matched_keyword": keyword}

    for keyword in CENTRAL_SOE_KEYWORDS:
        if keyword in text:
            return {"ownership": "central_soe", "confidence": 0.75, "matched_keyword": keyword}

    for keyword in LOCAL_SOE_KEYWORDS:
        if keyword in text:
            return {"ownership": "local_soe", "confidence": 0.65, "matched_keyword": keyword}

    for keyword in PRIVATE_DEVELOPER_KEYWORDS:
        if keyword in text:
            return {"ownership": "private", "confidence": 0.65, "matched_keyword": keyword}

    return {"ownership": "unknown", "confidence": 0.3, "matched_keyword": None}


def classify_land_buyer(raw: Dict) -> Dict[str, object]:
    buyer = raw.get("buyer") or raw.get("jdr") or raw.get("winner") or raw.get("companyName") or raw.get("竞得人")
    result = classify_company_ownership(buyer)
    result["buyer"] = buyer
    return result
