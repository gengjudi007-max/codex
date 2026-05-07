from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from codex.services.risk_chain import analyze_risk_chain
from codex.services.text_utils import infer_city, infer_company, normalize_text, unique

DEFAULT_MEMORY_PATH = "data/memory_events.jsonl"
EVENT_FIELDS = ("title", "summary", "content", "text", "message")
RISK_TERMS = [
    "城投托底", "土地财政", "库存去化", "减值", "流动性", "债务重组", "保交楼",
    "白名单", "收储", "退出低效项目", "应收账款", "经营现金流", "合理控制新增房地产用地供应",
]


def remember_event(event: Dict[str, Any], path: str = DEFAULT_MEMORY_PATH) -> Dict[str, Any]:
    normalized = normalize_event(event)
    file_path = Path(path).expanduser()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    existing_ids = {item.get("id") for item in iter_memory(path)}
    if normalized["id"] in existing_ids:
        return {"path": str(file_path), "written": 0, "event": normalized}
    with file_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(normalized, ensure_ascii=False) + "\n")
    return {"path": str(file_path), "written": 1, "event": normalized}


def remember_events(events: Iterable[Dict[str, Any]], path: str = DEFAULT_MEMORY_PATH) -> Dict[str, Any]:
    written = 0
    stored = []
    for event in events:
        if not isinstance(event, dict):
            continue
        result = remember_event(event, path=path)
        written += int(result["written"])
        stored.append(result["event"])
    return {"path": str(Path(path).expanduser()), "written": written, "events": stored}


def normalize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    text = _event_text(event)
    occurred_at = str(event.get("occurred_at") or event.get("date") or _extract_date(text) or "")
    city = event.get("city") or infer_city(text)
    company = event.get("company") or infer_company(text)
    risks = _extract_risks(text)
    risk_chain = analyze_risk_chain(event)
    normalized = dict(event)
    normalized.update(
        {
            "id": event.get("id") or _event_id(text, occurred_at, city, company),
            "title": event.get("title") or _compact(text, 80) or "未命名事件",
            "summary": event.get("summary") or _compact(text, 200),
            "occurred_at": occurred_at,
            "city": city,
            "company": company,
            "risks": risks,
            "risk_chains": [chain["chain"] for chain in risk_chain.get("chains", [])],
            "entities": unique([value for value in (city, company) if value] + risks),
            "stored_at": event.get("stored_at") or datetime.now(timezone.utc).isoformat(),
        }
    )
    return normalized


def iter_memory(path: str = DEFAULT_MEMORY_PATH) -> Iterable[Dict[str, Any]]:
    file_path = Path(path).expanduser()
    if not file_path.exists():
        return []
    with file_path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def query_memory(
    query: str = "",
    path: str = DEFAULT_MEMORY_PATH,
    entity: str = "",
    limit: int = 20,
) -> Dict[str, Any]:
    terms = [term for term in normalize_text(query).split() if term]
    entity = normalize_text(entity)
    matched = []
    for event in iter_memory(path):
        haystack = normalize_text(" ".join(str(event.get(field, "")) for field in EVENT_FIELDS) + " " + " ".join(event.get("entities", [])))
        if entity and entity not in haystack:
            continue
        if terms and not all(term in haystack for term in terms):
            continue
        matched.append(event)
    matched = sorted(matched, key=lambda item: str(item.get("occurred_at") or item.get("stored_at") or ""), reverse=True)
    return {
        "path": str(Path(path).expanduser()),
        "query": query,
        "entity": entity,
        "matched": len(matched),
        "events": matched[:limit],
    }


def build_timeline(entity: str, path: str = DEFAULT_MEMORY_PATH, limit: int = 50) -> Dict[str, Any]:
    result = query_memory(entity=entity, path=path, limit=limit)
    events = sorted(result["events"], key=lambda item: str(item.get("occurred_at") or item.get("stored_at") or ""))
    return {
        "entity": entity,
        "path": result["path"],
        "event_count": len(events),
        "timeline": [
            {
                "occurred_at": event.get("occurred_at"),
                "title": event.get("title"),
                "summary": event.get("summary"),
                "city": event.get("city"),
                "company": event.get("company"),
                "risks": event.get("risks", []),
                "risk_chains": event.get("risk_chains", []),
            }
            for event in events
        ],
    }


def link_related_events(event: Dict[str, Any], path: str = DEFAULT_MEMORY_PATH, limit: int = 10) -> Dict[str, Any]:
    normalized = normalize_event(event)
    candidates = []
    for stored in iter_memory(path):
        score = _relation_score(normalized, stored)
        if score > 0:
            candidates.append({"score": score, "event": stored, "shared": _shared_entities(normalized, stored)})
    candidates = sorted(candidates, key=lambda item: item["score"], reverse=True)
    return {
        "input_event": normalized,
        "related_count": len(candidates),
        "related_events": candidates[:limit],
        "claim_boundary": "关联结果基于实体、风险词和风险链的规则匹配，只提示追踪方向，不代表因果关系已被证实。",
    }


def memory_summary(path: str = DEFAULT_MEMORY_PATH) -> Dict[str, Any]:
    events = list(iter_memory(path))
    entities = []
    risks = []
    chains = []
    for event in events:
        entities.extend(event.get("entities", []))
        risks.extend(event.get("risks", []))
        chains.extend(event.get("risk_chains", []))
    return {
        "path": str(Path(path).expanduser()),
        "event_count": len(events),
        "entities": unique(entities),
        "risks": unique(risks),
        "risk_chains": unique(chains),
    }


def _event_text(event: Dict[str, Any]) -> str:
    return normalize_text(" ".join(str(event.get(field, "")) for field in EVENT_FIELDS))


def _extract_risks(text: str) -> List[str]:
    return unique(term for term in RISK_TERMS if term in text)


def _extract_date(text: str) -> str:
    match = re.search(r"(20\d{2})年(?:([01]?\d)月)?(?:([0-3]?\d)日)?", text)
    if not match:
        return ""
    year, month, day = match.groups()
    if month and day:
        return f"{year}-{int(month):02d}-{int(day):02d}"
    if month:
        return f"{year}-{int(month):02d}"
    return year


def _event_id(text: str, occurred_at: str, city: Any, company: Any) -> str:
    import hashlib

    basis = "|".join([normalize_text(text), str(occurred_at), str(city or ""), str(company or "")])
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]


def _compact(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "..."


def _relation_score(a: Dict[str, Any], b: Dict[str, Any]) -> int:
    score = 0
    score += len(set(a.get("entities", [])) & set(b.get("entities", []))) * 20
    score += len(set(a.get("risks", [])) & set(b.get("risks", []))) * 15
    score += len(set(a.get("risk_chains", [])) & set(b.get("risk_chains", []))) * 25
    if a.get("city") and a.get("city") == b.get("city"):
        score += 15
    if a.get("company") and a.get("company") == b.get("company"):
        score += 15
    return min(score, 100)


def _shared_entities(a: Dict[str, Any], b: Dict[str, Any]) -> List[str]:
    return unique(list(set(a.get("entities", [])) & set(b.get("entities", []))))
