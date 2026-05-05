from __future__ import annotations

import json
import subprocess
import warnings
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning


BASE_URL = "https://biz.ghzyj.sh.gov.cn"
SOURCE = "上海土地市场"
REFERER = "https://biz.ghzyj.sh.gov.cn/shtdsc/jy/view/web/transaction/result/list_result_ywtb.html?tabIndex=1"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147 Safari/537.36",
    "Referer": REFERER,
    "Origin": BASE_URL,
    "Accept": "*/*",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
}


def fetch_shanghai_land_items(
    api_url: str,
    payload: Optional[Dict[str, Any]] = None,
    max_pages: int = 1,
    verify_ssl: bool = False,
    use_curl_fallback: bool = True,
) -> List[Dict[str, Any]]:
    """抓取上海土地成交列表。

    上海站点存在旧式TLS兼容问题。requests 失败时可回退到系统 curl。
    """
    results: List[Dict[str, Any]] = []
    payload = payload or default_payload()

    if not verify_ssl:
        warnings.simplefilter("ignore", InsecureRequestWarning)

    for page in range(1, max_pages + 1):
        page_payload = dict(payload)
        page_payload.setdefault("page", page)
        page_payload.setdefault("limit", 10)
        data = fetch_page(api_url, page_payload, verify_ssl=verify_ssl, use_curl_fallback=use_curl_fallback)
        rows = extract_rows(data)
        if not rows:
            break
        for row in rows:
            item = normalize_row(row)
            if item:
                results.append(item)
    return results


def fetch_page(
    api_url: str,
    payload: Dict[str, Any],
    verify_ssl: bool = False,
    use_curl_fallback: bool = True,
) -> Dict[str, Any]:
    try:
        response = requests.post(
            api_url,
            data=payload,
            headers=HEADERS,
            timeout=15,
            verify=verify_ssl,
        )
        response.raise_for_status()
        return safe_json_text(response.text)
    except requests.exceptions.SSLError:
        if not use_curl_fallback:
            raise
        return fetch_page_with_curl(api_url, payload)


def fetch_page_with_curl(api_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    data = urlencode(payload)
    cmd = [
        "curl",
        "-k",
        "--silent",
        "--show-error",
        "--location",
        api_url,
        "-H", f"User-Agent: {HEADERS['User-Agent']}",
        "-H", f"Referer: {HEADERS['Referer']}",
        "-H", f"Origin: {HEADERS['Origin']}",
        "-H", f"Accept: {HEADERS['Accept']}",
        "-H", f"Content-Type: {HEADERS['Content-Type']}",
        "-H", f"X-Requested-With: {HEADERS['X-Requested-With']}",
        "--data-raw", data,
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return safe_json_text(completed.stdout)


def default_payload() -> Dict[str, Any]:
    return {
        "page": 1,
        "limit": 10,
    }


def safe_json_text(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    try:
        return json.loads(text)
    except Exception:
        return {"raw_text": text}


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


def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    land_name = pick(row, ["title", "landName", "zdmc", "xmmc", "name", "noticeTitle"])
    district = pick(row, ["county", "district", "qx", "xzq", "regionName"])
    land_use = pick(row, ["landuse", "landUse", "tdyt", "ghyt", "useType"])
    date = pick(row, ["date", "cjsj", "fbsj", "pubdate", "createTime", "dealTime"])
    buyer = pick(row, ["buyer", "jdr", "竞得人", "companyName", "winner"])

    metrics = {}
    for key, aliases in {
        "land_area": ["tdmj", "ydmj", "landArea", "area"],
        "planned_gfa": ["jzmj", "ghjzmj", "buildingArea", "gfa"],
        "land_amount": ["cjj", "cjje", "price", "amount", "dealPrice"],
        "floor_price": ["floorPrice", "loudijia", "cjlmj"],
        "premium_rate": ["premiumRate", "yjl", "premium"],
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
    if buyer:
        content_parts.append(f"竞得方为{buyer}")

    return {
        "category": "land",
        "title": land_name or "上海土地成交项目",
        "content": "，".join(content_parts) + "。" if content_parts else "上海土地成交项目。",
        "city": "上海",
        "date": date,
        "source": SOURCE,
        "source_level": "level_2",
        "verified": True,
        "metrics": metrics,
        "raw": row,
    }


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
