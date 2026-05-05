from __future__ import annotations

import re
from typing import Dict, List

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://yewu.ghzrzyw.beijing.gov.cn"
LIST_URL = f"{BASE_URL}/gwxxfb/tdsc/tdzpgxm.html"


def fetch_beijing_land_items(max_pages: int = 3) -> List[Dict]:
    """抓取北京土地成交列表（简化版HTML解析）"""
    results: List[Dict] = []

    for page in range(1, max_pages + 1):
        url = LIST_URL if page == 1 else f"{LIST_URL}?page={page}"
        resp = requests.get(url, timeout=10)
        resp.encoding = "utf-8"

        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table")
        if not table:
            continue

        rows = table.find_all("tr")
        for tr in rows[1:]:
            cols = [td.get_text(strip=True) for td in tr.find_all("td")]
            if len(cols) < 5:
                continue

            item = parse_row(cols)
            if item:
                results.append(item)

    return results


def parse_row(cols: List[str]) -> Dict:
    """根据北京土地页面表格结构解析字段（需根据实际结构微调）"""
    try:
        return {
            "city": "北京",
            "land_name": cols[0],
            "district": cols[1] if len(cols) > 1 else None,
            "land_use": cols[2] if len(cols) > 2 else None,
            "transaction_status": cols[3] if len(cols) > 3 else None,
            "transaction_date": extract_date(cols),
            "raw_text": " | ".join(cols),
            "source": "北京市规划和自然资源委员会",
        }
    except Exception:
        return {}


def extract_date(cols: List[str]) -> str:
    for text in cols:
        match = re.search(r"\d{4}-\d{2}-\d{2}", text)
        if match:
            return match.group(0)
    return ""
