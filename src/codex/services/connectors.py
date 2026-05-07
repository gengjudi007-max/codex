from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Dict, List

from codex.services.data_fetcher import fetch_source_dicts
from codex.services.reliability import cache_get, cache_key, cache_set, retry
from codex.services.text_utils import compact_text, infer_city, infer_company, normalize_text

CONNECTOR_TYPES = {
    "exchange_filing": "交易所公告",
    "hkex_filing": "港交所公告",
    "sse_filing": "上交所公告",
    "szse_filing": "深交所公告",
    "land_transaction": "土地公告",
    "bond_prospectus": "债券/专项债募集说明书",
    "policy": "政策文件",
    "company_ir": "公司投资者关系",
    "research_report": "第三方研究报告",
    "generic_web": "通用网页",
}


@dataclass
class ConnectorSpec:
    name: str
    connector_type: str
    url: str
    keywords: List[str]
    source_type: str = "generic_web"
    cache: bool = True
    timeout: int = 15
    attempts: int = 2


def run_connectors(config: Dict[str, Any]) -> Dict[str, Any]:
    specs = [_spec(item) for item in config.get("connectors", []) if isinstance(item, dict)]
    results = []
    errors = []
    for spec in specs:
        result = run_connector(spec)
        if result.get("status") == "failed":
            errors.append(result)
        else:
            results.append(result)
    return {
        "mode": "real_time_connectors",
        "connector_count": len(specs),
        "success_count": len(results),
        "error_count": len(errors),
        "items": results,
        "errors": errors,
    }


def run_connector(spec: ConnectorSpec) -> Dict[str, Any]:
    key = cache_key("connector", spec.connector_type, spec.url, spec.keywords)
    cached = cache_get(key) if spec.cache else None

    try:
        fetched = retry(
            lambda: fetch_source_dicts([
                {"name": spec.name, "url": spec.url, "source_type": spec.source_type}
            ], timeout=spec.timeout),
            attempts=spec.attempts,
            delay_seconds=1.0,
        )
        raw = fetched[0] if fetched else {"status": "failed", "error": "empty response"}
    except Exception as exc:  # noqa: BLE001
        return _failed(spec, str(exc), cached)

    if raw.get("status") == "failed":
        return _failed(spec, raw.get("error") or "fetch failed", cached)

    item = _normalize_connector_item(spec, raw)
    previous = cached.get("value") if cached else None
    diff = detect_change(previous, item) if previous else {"changed": True, "reason": "first_seen"}
    if spec.cache:
        cache_set(key, item)

    item["change"] = diff
    return item


def detect_change(previous: Dict[str, Any] | None, current: Dict[str, Any]) -> Dict[str, Any]:
    if not previous:
        return {"changed": True, "reason": "first_seen"}
    prev_hash = previous.get("content_hash")
    current_hash = current.get("content_hash")
    if prev_hash != current_hash:
        return {
            "changed": True,
            "reason": "content_hash_changed",
            "previous_hash": prev_hash,
            "current_hash": current_hash,
        }
    return {"changed": False, "reason": "unchanged"}


def connector_items_to_sources(connector_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [item for item in connector_result.get("items", []) if isinstance(item, dict)]


def _spec(item: Dict[str, Any]) -> ConnectorSpec:
    connector_type = str(item.get("connector_type") or item.get("type") or "generic_web")
    return ConnectorSpec(
        name=str(item.get("name") or item.get("title") or connector_type),
        connector_type=connector_type,
        url=str(item.get("url") or ""),
        keywords=[str(keyword) for keyword in item.get("keywords", [])],
        source_type=str(item.get("source_type") or _source_type_for_connector(connector_type)),
        cache=bool(item.get("cache", True)),
        timeout=int(item.get("timeout", 15)),
        attempts=int(item.get("attempts", 2)),
    )


def _source_type_for_connector(connector_type: str) -> str:
    if "filing" in connector_type:
        return "exchange_filing"
    if "land" in connector_type:
        return "land_transaction"
    if "bond" in connector_type:
        return "bond_prospectus"
    if "policy" in connector_type:
        return "policy"
    if "research" in connector_type:
        return "research_report"
    return "media_report"


def _normalize_connector_item(spec: ConnectorSpec, raw: Dict[str, Any]) -> Dict[str, Any]:
    content = normalize_text(raw.get("content") or raw.get("summary") or raw.get("text") or "")
    keyword_hits = [keyword for keyword in spec.keywords if keyword and keyword in content]
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return {
        "status": "ok",
        "connector_type": spec.connector_type,
        "connector_label": CONNECTOR_TYPES.get(spec.connector_type, spec.connector_type),
        "source_type": spec.source_type,
        "source": spec.name,
        "url": spec.url,
        "title": raw.get("title") or spec.name,
        "summary": compact_text(content, 500),
        "content": content,
        "city": infer_city(content),
        "company": infer_company(content),
        "keyword_hits": keyword_hits,
        "content_hash": content_hash,
        "signal_strength": _signal_strength(keyword_hits, content),
    }


def _signal_strength(keyword_hits: List[str], content: str) -> Dict[str, Any]:
    risk_terms = ["风险", "亏损", "减值", "债务", "收储", "城投", "流拍", "底价", "止跌回稳"]
    risk_hits = [term for term in risk_terms if term in content]
    score = min(len(keyword_hits) * 20 + len(risk_hits) * 12, 100)
    if score >= 70:
        level = "high"
    elif score >= 35:
        level = "medium"
    else:
        level = "low"
    return {"score": score, "level": level, "risk_hits": risk_hits}


def _failed(spec: ConnectorSpec, error: str, cached: Dict[str, Any] | None) -> Dict[str, Any]:
    fallback = cached.get("value") if cached else None
    return {
        "status": "failed",
        "connector_type": spec.connector_type,
        "source": spec.name,
        "url": spec.url,
        "error": error,
        "fallback_available": fallback is not None,
        "fallback": fallback,
    }
