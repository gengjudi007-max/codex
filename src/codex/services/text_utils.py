from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional


KNOWN_CITIES = [
    "北京", "上海", "广州", "深圳", "杭州", "南京", "苏州", "武汉", "成都", "重庆",
    "天津", "西安", "郑州", "长沙", "合肥", "宁波", "厦门", "福州", "青岛", "济南",
    "沈阳", "大连", "长春", "哈尔滨", "昆明", "南宁", "贵阳", "南昌", "太原", "石家庄",
    "无锡", "常州", "佛山", "东莞", "珠海", "温州", "嘉兴", "绍兴", "徐州", "泉州",
]

KNOWN_COMPANIES = [
    "保利发展", "万科", "招商蛇口", "华润置地", "中国海外发展", "中海地产", "绿城中国",
    "滨江集团", "龙湖集团", "金地集团", "建发国际", "越秀地产", "华发股份", "新城控股",
    "碧桂园", "融创中国", "旭辉控股", "远洋集团", "金茂", "中国金茂", "绿地控股",
]


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(normalize_text(item) for item in value)
    return re.sub(r"\s+", " ", str(value)).strip()


def compact_text(value: Any, limit: int = 120) -> str:
    text = normalize_text(value)
    return text if len(text) <= limit else text[: limit - 1] + "..."


def infer_city(text: str) -> Optional[str]:
    normalized = normalize_text(text)
    for city in KNOWN_CITIES:
        if city in normalized:
            return city
    match = re.search(r"([\u4e00-\u9fa5]{2,6})(?:市)?(?:土拍|土地|楼市|房价|成交|供地)", normalized)
    return match.group(1) if match else None


def infer_company(text: str) -> Optional[str]:
    normalized = normalize_text(text)
    for company in KNOWN_COMPANIES:
        if company in normalized:
            return company
    match = re.search(r"([\u4e00-\u9fa5A-Za-z0-9]{2,12})(?:发布|公告|年报|净利润|亏损|融资|拿地)", normalized)
    return match.group(1) if match else None


def infer_region(text: str) -> Optional[str]:
    normalized = normalize_text(text)
    match = re.search(r"([\u4e00-\u9fa5]{2,8})(?:区域|片区|板块|新区)", normalized)
    return match.group(1) if match else None


def unique(items: Iterable[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        normalized = normalize_text(item)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result
