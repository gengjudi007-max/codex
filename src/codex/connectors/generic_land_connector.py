from __future__ import annotations

from typing import Dict, List

import requests
from bs4 import BeautifulSoup

from codex.connectors.city_land_sources import CityLandSource


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
}


def fetch_generic_html_table(source: CityLandSource, max_pages: int = 2) -> List[Dict]:
    """通用HTML表格抓取器（适用于结构简单页面）"""
    results: List[Dict] = []

    for page in range(1, max_pages + 1):
        url = source.url
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.encoding = "utf-8"
        except Exception:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table")
        if not table:
            continue

        rows = table.find_all("tr")
        for tr in rows[1:]:
            cols = [td.get_text(strip=True) for td in tr.find_all("td")]
            if not cols:
                continue

            results.append({
                "city": source.city,
                "raw_cols": cols,
                "source": source.source,
                "source_level": source.source_level,
            })

    return results
