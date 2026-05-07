from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List


def item_id(item: Dict[str, Any]) -> str:
    basis = "|".join(
        str(item.get(key, ""))
        for key in ("source", "url", "source_file", "title", "published_at", "summary")
    )
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]


def dedupe_items(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    result = []
    for item in items:
        key = item_id(item)
        if key in seen:
            continue
        seen.add(key)
        enriched = dict(item)
        enriched.setdefault("id", key)
        result.append(enriched)
    return result


def append_jsonl(path: str, items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    file_path = Path(path).expanduser()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    existing_ids = {item.get("id") for item in iter_jsonl(str(file_path))}
    written = 0
    with file_path.open("a", encoding="utf-8") as handle:
        for item in dedupe_items(items):
            if item["id"] in existing_ids:
                continue
            record = dict(item)
            record.setdefault("stored_at", datetime.now(timezone.utc).isoformat())
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            existing_ids.add(item["id"])
            written += 1
    return {"path": str(file_path), "written": written, "total": len(existing_ids)}


def write_jsonl(path: str, items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    file_path = Path(path).expanduser()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    unique_items = dedupe_items(items)
    with file_path.open("w", encoding="utf-8") as handle:
        for item in unique_items:
            record = dict(item)
            record.setdefault("stored_at", datetime.now(timezone.utc).isoformat())
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {"path": str(file_path), "written": len(unique_items), "total": len(unique_items)}


def write_jsonl_stream(path: str, items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    file_path = Path(path).expanduser()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    seen = set()
    written = 0
    with file_path.open("w", encoding="utf-8") as handle:
        for item in items:
            if not isinstance(item, dict):
                continue
            key = item_id(item)
            if key in seen:
                continue
            seen.add(key)
            record = dict(item)
            record.setdefault("id", key)
            record.setdefault("stored_at", datetime.now(timezone.utc).isoformat())
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1
    return {"path": str(file_path), "written": written, "total": written}


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    return list(iter_jsonl(path))


def iter_jsonl(path: str) -> Iterator[Dict[str, Any]]:
    file_path = Path(path).expanduser()
    if not file_path.exists():
        return
    with file_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def summarize_jsonl(path: str) -> Dict[str, Any]:
    total = 0
    source_counts: Dict[str, int] = {}
    status_counts: Dict[str, int] = {}
    file_type_counts: Dict[str, int] = {}
    for item in iter_jsonl(path):
        total += 1
        _increment(source_counts, str(item.get("source") or ""))
        _increment(status_counts, str(item.get("status") or ""))
        _increment(file_type_counts, str(item.get("file_type") or ""))
    return {
        "path": str(Path(path).expanduser()),
        "total": total,
        "source_counts": source_counts,
        "status_counts": status_counts,
        "file_type_counts": file_type_counts,
    }


def search_jsonl(
    path: str,
    query: str,
    limit: int = 20,
    offset: int = 0,
    fields: Iterable[str] | None = None,
) -> Dict[str, Any]:
    terms = [term.lower() for term in query.split() if term.strip()]
    selected_fields = tuple(fields or ("title", "summary", "content", "source_file", "company", "city"))
    matches: List[Dict[str, Any]] = []
    matched = 0
    scanned = 0
    for item in iter_jsonl(path):
        scanned += 1
        haystack = " ".join(str(item.get(field, "")) for field in selected_fields).lower()
        if terms and not all(term in haystack for term in terms):
            continue
        if not terms and query.strip():
            continue
        matched += 1
        if matched <= offset:
            continue
        if len(matches) < limit:
            matches.append(_search_result_item(item))
    return {
        "path": str(Path(path).expanduser()),
        "query": query,
        "scanned": scanned,
        "matched": matched,
        "returned": len(matches),
        "offset": offset,
        "limit": limit,
        "items": matches,
    }


def _search_result_item(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": item.get("id"),
        "source": item.get("source"),
        "title": item.get("title"),
        "summary": item.get("summary"),
        "source_file": item.get("source_file"),
        "source_folder": item.get("source_folder"),
        "file_type": item.get("file_type"),
        "city": item.get("city"),
        "company": item.get("company"),
        "status": item.get("status"),
        "metrics": item.get("metrics"),
    }


def _increment(counts: Dict[str, int], key: str) -> None:
    key = key or "unknown"
    counts[key] = counts.get(key, 0) + 1
