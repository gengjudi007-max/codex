from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from codex.services.data_fetcher import fetch_source_dicts
from codex.services.document_parser import parse_documents
from codex.services.memory_graph import remember_events
from codex.services.source_store import append_jsonl
from codex.services.text_utils import compact_text, infer_city, infer_company, normalize_text

SOURCE_TYPES = {
    "policy": "政策文件",
    "exchange_filing": "交易所公告",
    "annual_report": "年报/财报",
    "land_transaction": "土地成交",
    "bond_prospectus": "专项债/债券募集说明书",
    "research_report": "第三方机构报告",
    "media_report": "公开报道",
    "local_note": "本地素材",
    "interview_note": "采访记录",
}

DEFAULT_STORE_PATH = "data/source_items.jsonl"
DEFAULT_MEMORY_PATH = "data/memory_events.jsonl"


def ingest_sources(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Unified source ingestion entrypoint.

    Accepts urls, local paths, raw text snippets, and structured items, then stores
    normalized items and memory events. It never fabricates missing content.
    """
    store_path = str(payload.get("store_path") or DEFAULT_STORE_PATH)
    memory_path = str(payload.get("memory_path") or DEFAULT_MEMORY_PATH)
    items: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    raw_items = payload.get("items") or []
    if isinstance(raw_items, list):
        items.extend(_normalize_item(item, source_hint="structured") for item in raw_items if isinstance(item, dict))

    texts = payload.get("texts") or []
    if isinstance(texts, list):
        items.extend(_normalize_text_item(text, source_type="local_note") for text in texts if normalize_text(text))

    sources = payload.get("sources") or []
    if isinstance(sources, list) and sources:
        fetched = fetch_source_dicts(sources, timeout=int(payload.get("timeout", 15)))
        for result in fetched:
            if result.get("status") == "failed":
                errors.append(result)
            else:
                items.append(_normalize_item(result, source_hint="url"))

    paths = payload.get("paths") or []
    if isinstance(paths, list) and paths:
        try:
            parsed = parse_documents(paths, source=str(payload.get("source") or "document"))
            items.extend(_normalize_item(item, source_hint="document") for item in parsed)
        except Exception as exc:  # noqa: BLE001
            errors.append({"source": "document", "status": "failed", "error": str(exc)})

    unique_items = _dedupe(items)
    store_result = append_jsonl(store_path, unique_items) if unique_items else {"path": store_path, "written": 0, "total": 0}
    memory_result = remember_events(unique_items, path=memory_path) if unique_items else {"path": memory_path, "written": 0, "events": []}

    return {
        "mode": "source_ingestion",
        "accepted_count": len(unique_items),
        "error_count": len(errors),
        "items": unique_items,
        "errors": errors,
        "store": store_result,
        "memory": memory_result,
        "source_type_catalog": SOURCE_TYPES,
        "next_actions": _next_actions(unique_items, errors),
    }


def _normalize_item(item: Dict[str, Any], source_hint: str = "unknown") -> Dict[str, Any]:
    text = normalize_text(" ".join(str(item.get(key, "")) for key in ("title", "summary", "content", "text", "message")))
    source_type = str(item.get("source_type") or item.get("type") or _infer_source_type(item, text))
    normalized = dict(item)
    normalized.update(
        {
            "source_type": source_type,
            "source_label": SOURCE_TYPES.get(source_type, source_type),
            "source_hint": source_hint,
            "title": item.get("title") or compact_text(text, 80) or "未命名信息源",
            "summary": item.get("summary") or compact_text(text, 300),
            "content": item.get("content") or item.get("text") or text,
            "city": item.get("city") or infer_city(text),
            "company": item.get("company") or infer_company(text),
            "ingested_at": item.get("ingested_at") or datetime.now(timezone.utc).isoformat(),
            "verification_status": item.get("verification_status") or "source_collected",
        }
    )
    return normalized


def _normalize_text_item(text: Any, source_type: str = "local_note") -> Dict[str, Any]:
    normalized = normalize_text(text)
    return _normalize_item(
        {
            "source_type": source_type,
            "title": compact_text(normalized, 80),
            "summary": compact_text(normalized, 300),
            "content": normalized,
            "source": "local_text",
        },
        source_hint="text",
    )


def _infer_source_type(item: Dict[str, Any], text: str) -> str:
    source = " ".join(str(item.get(key, "")) for key in ("source", "name", "url", "title")) + " " + text
    if "自然资源" in source or "土地" in source or "土拍" in source:
        return "land_transaction"
    if "年报" in source or "财报" in source:
        return "annual_report"
    if "交易所" in source or "公告" in source:
        return "exchange_filing"
    if "专项债" in source or "募集说明书" in source:
        return "bond_prospectus"
    if "政策" in source or "会议" in source:
        return "policy"
    if "研究" in source or "报告" in source:
        return "research_report"
    return "local_note"


def _dedupe(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    result = []
    for item in items:
        key = "|".join(str(item.get(field, "")) for field in ("source_type", "url", "title", "summary"))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _next_actions(items: List[Dict[str, Any]], errors: List[Dict[str, Any]]) -> List[str]:
    actions = []
    if items:
        actions.append("进入 signal_monitor、topic_pipeline、risk_chain 和 fact_check 流程。")
    if errors:
        actions.append("检查失败数据源的 URL、登录权限、反爬限制或本地文件路径。")
    actions.append("为核心数字补充一手来源，并记录统计口径。")
    return actions
