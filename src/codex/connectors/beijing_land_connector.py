from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional


BASE_URL = "https://yewu.ghzrzyw.beijing.gov.cn"
API_URL = f"{BASE_URL}/zkdncms/tdgltdsc/tdzpgxm/esSearchList"
SOURCE = "北京市规划和自然资源委员会"

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
        "landusetype1": "",
        "announcetype": "",
        "county": "",
        "gjz": "",
        "_": timestamp,
    }
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode('utf-8'))


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
    land_use = pick(row, ["landusetype1", "landuse", "landUse", "tdyt", "ghyt", "yt"])
    status = pick(row, ["status", "jyzt", "zt", "announcetype", "gglx"])
    date = pick(row, ["date", "cjsj", "jzsj", "fbsj", "pubdate", "createTime", "createDateTime", "publishTime", "executiondate", "startdate"])
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
