from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import re

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None


@dataclass
class DataSource:
    """公开信息源配置。"""

    name: str
    source_type: str
    url: str
    region: Optional[str] = None
    company: Optional[str] = None
    parser: str = "plain_text"


class DataFetchError(RuntimeError):
    pass


def fetch_sources(sources: List[DataSource], timeout: int = 15) -> List[Dict[str, Any]]:
    """抓取公开信息源，并统一为系统输入格式。

    注意：该函数只负责抓取与基础清洗，不做事实推断。
    若网页反爬、登录限制或格式异常，应返回明确错误，避免生成伪数据。
    """
    results = []
    for source in sources:
        try:
            results.append(fetch_source(source, timeout=timeout))
        except Exception as exc:  # noqa: BLE001
            results.append(
                {
                    "type": source.source_type,
                    "title": source.name,
                    "source": source.name,
                    "url": source.url,
                    "region": source.region,
                    "company": source.company,
                    "content": "",
                    "metrics": {},
                    "status": "failed",
                    "error": str(exc),
                }
            )
    return results


def fetch_source(source: DataSource, timeout: int = 15) -> Dict[str, Any]:
    if requests is None:
        raise DataFetchError("requests is not installed. Run: pip install requests beautifulsoup4")

    response = requests.get(
        source.url,
        timeout=timeout,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; CodexRealEstateReporter/0.1)",
        },
    )
    response.raise_for_status()

    text = _extract_text(response.text)
    metrics = extract_basic_metrics(text)

    return {
        "type": source.source_type,
        "title": _infer_title(text) or source.name,
        "source": source.name,
        "url": source.url,
        "region": source.region,
        "company": source.company,
        "content": text,
        "summary": text[:500],
        "metrics": metrics,
        "status": "ok",
    }


def extract_basic_metrics(text: str) -> Dict[str, Any]:
    """从文本中抽取基础数值线索。

    第一版采用稳健的正则抽取，后续可替换为面向公告/政策/土地的专门 parser。
    """
    metrics: Dict[str, Any] = {
        "amounts_yi": [],
        "percentages": [],
        "areas_wan_sqm": [],
    }

    for match in re.finditer(r"([0-9]+(?:\.[0-9]+)?)\s*亿元", text):
        metrics["amounts_yi"].append(float(match.group(1)))

    for match in re.finditer(r"([+-]?[0-9]+(?:\.[0-9]+)?)\s*%", text):
        metrics["percentages"].append(float(match.group(1)))

    for match in re.finditer(r"([0-9]+(?:\.[0-9]+)?)\s*万(?:平方米|㎡|平米)", text):
        metrics["areas_wan_sqm"].append(float(match.group(1)))

    return metrics


def _extract_text(html_or_text: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", html_or_text, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _infer_title(text: str) -> Optional[str]:
    if not text:
        return None
    title = text[:80].strip()
    return title if title else None
