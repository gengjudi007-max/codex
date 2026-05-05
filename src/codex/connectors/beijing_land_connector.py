from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import requests


BASE_URL = "https://yewu.ghzrzyw.beijing.gov.cn"
SOURCE = "北京市规划和自然资源委员会"

API_CANDIDATES = [
    f"{BASE_URL}/esSearchList",
    f"{BASE_URL}/gwxxfb/esSearchList",
    f"{BASE_URL}/gwxxfb/tdsc/esSearchList",
    f"{BASE_URL}/gwxxfb/tdsc/esSearchList.do",
    f"{BASE_URL}/gwxxfb/tdsc/esSearchList.json",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Referer": f"{BASE_URL}/gwxxfb/tdsc/tdzpgxm.html",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
}


def fetch_beijing_land_items(max_pages: int = 3, limit: int = 10) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    for page in range(1, max_pages + 1):
        payload = fetch_beijing_land_page(page=page, limit=limit)
        rows = extract_rows(payload)
        if not rows:
            break
        for row in rows:
            item = normalize_api_row(row)
            if item:
                results.append(item)
    return results


def fetch_beijing_land_page(page: int = 1, limit: int = 10) -> Dict[str, Any]:
    timestamp = int(time.time() * 1000)
    params = {
        "t": timestamp,
        "page": page,
        "limit": limit,
        "landuse": "",
        "type1": "",
        "announcetype": "",
        "county": "",
        "gjz": "",
        "_": timestamp + 1,
    }
    errors = []
    for api_url in API_CANDIDATES:
        try:
            resp = requests.get(api_url, params=params, headers=HEADERS, timeout=15)
            if resp.status_code == 404:
                errors.append(f"404 {resp.url}")
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            errors.append(f"{api_url}: {exc}")
            continue
    raise RuntimeError("北京土地接口候选地址均失败：\n" + "\n".join(errors))


def extract_rows(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ["data", "rows", "list", "result"]:
        value = payload.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            for nested_key in ["data", "rows", "list", "records"]:
                nested = value.get(nested_key)
                if isinstance(nested, list):
                    return nested
    return []


def normalize_api_row(row: Dict[str, Any]) -> Dict[str, Any]:
    land_name = pick(row, ["title", "landName", "zdmc", "xmmc", "name", "bt"])
    district = pick(row, ["county", "district", "qx", "xzq", "qymc"])
    land_use = pick(row, ["landuse", "landUse", "tdyt", "ghyt", "yt"])
    status = pick(row, ["status", "jyzt", "zt", "announcetype", "gglx"])
    date = pick(row, ["date", "cjsj", "jzsj", "fbsj", "pubdate", "createTime"])
    url = build_detail_url(row)

    metrics = {}
    for key, aliases in {
        "land_area": ["ydmj", "tdmj", "landArea", "area"],
        "planned_gfa": ["jzmj", "ghjzmj", "buildingArea", "gfa"],
        "land_amount": ["cjj", "cjje", "price", "amount"],
        "floor_price": ["loudijia", "floorPrice", "cjlmj"],
        "premium_rate": ["yjl", "premiumRate", "premium"],
    }.items():
        value = to_number(pick(row, aliases))
        if value is not None:
            metrics[key] = value

    content_parts = []
    if land_name:
        content_parts.append(f"地块名称为{land_name}")
    if district:
        content_parts.append(f"所在区域为{district}")
    if land_use:
        content_parts.append(f"规划用途为{land_use}")
    if status:
        content_parts.append(f"交易状态为{status}")

    return {
        "category": "land",
        "title": land_name or "北京土地市场项目",
        "content": "，".join(content_parts) + "。" if content_parts else "北京土地市场项目。",
        "city": "北京",
        "date": date,
        "source": SOURCE,
        "source_level": "level_2",
        "url": url,
        "verified": True,
        "metrics": metrics,
        "raw": row,
    }


def build_detail_url(row: Dict[str, Any]) -> Optional[str]:
    href = pick(row, ["url", "href", "link", "detailUrl"])
    if href:
        href = str(href)
        if href.startswith("http"):
            return href
        return BASE_URL + href if href.startswith("/") else f"{BASE_URL}/{href}"
    item_id = pick(row, ["id", "guid", "uuid", "objectid"])
    if item_id:
        return f"{BASE_URL}/gwxxfb/tdsc/{item_id}.html"
    return None


def pick(row: Dict[str, Any], keys: List[str]) -> Optional[Any]:
    for key in keys:
        if key in row and row[key] not in [None, ""]:
            return row[key]
    return None


def to_number(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "").replace("%", "")
    try:
        return float(text)
    except ValueError:
        return None
