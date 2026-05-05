from __future__ import annotations

from typing import Dict, List, Tuple

import requests
from bs4 import BeautifulSoup

from codex.connectors.city_land_sources import CityLandSource


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
}


def fetch_generic_html_table(source: CityLandSource, max_pages: int = 2) -> List[Dict]:
    """通用HTML表格抓取器（适用于结构简单页面）。

    如果返回0，通常说明页面是 JS/XHR 渲染，需要用浏览器 Network 找真实接口。
    """
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


def diagnose_html_source(source: CityLandSource) -> Dict:
    """诊断官方页面是否适合HTML表格抓取。"""
    try:
        resp = requests.get(source.url, headers=HEADERS, timeout=10)
        resp.encoding = "utf-8"
    except Exception as exc:
        return {
            "city": source.city,
            "url": source.url,
            "ok": False,
            "error": str(exc),
        }

    html = resp.text or ""
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    scripts = soup.find_all("script")
    links = soup.find_all("a")

    candidate_keywords = ["list", "query", "page", "td", "land", "地块", "成交", "出让"]
    candidate_scripts = []
    for script in scripts:
        text = script.get("src") or script.get_text(" ", strip=True)[:500]
        if any(keyword in text for keyword in candidate_keywords):
            candidate_scripts.append(text[:300])

    return {
        "city": source.city,
        "source": source.source,
        "url": source.url,
        "ok": resp.ok,
        "status_code": resp.status_code,
        "html_length": len(html),
        "table_count": len(tables),
        "link_count": len(links),
        "script_count": len(scripts),
        "title": soup.title.get_text(strip=True) if soup.title else None,
        "candidate_scripts": candidate_scripts[:10],
        "hint": "table_count=0 通常表示该页面需要XHR/API接口抓取。",
    }
