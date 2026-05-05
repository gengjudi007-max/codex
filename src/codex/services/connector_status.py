from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_STATUS_FILE = Path("data/storage/connector_status.json")


@dataclass
class ConnectorRunStatus:
    name: str
    city: Optional[str]
    category: str
    method: str
    status: str  # ok | empty | failed | semi_auto | skipped
    item_count: int = 0
    needs_cookie: bool = False
    needs_payload: bool = False
    error: Optional[str] = None
    last_run: str = datetime.now().isoformat(timespec="seconds")
    notes: Optional[str] = None


def load_connector_status(path: Path | str = DEFAULT_STATUS_FILE) -> Dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_connector_status(status_map: Dict[str, Any], path: Path | str = DEFAULT_STATUS_FILE) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(status_map, file, ensure_ascii=False, indent=2)
    return path


def update_connector_status(
    run_status: ConnectorRunStatus,
    path: Path | str = DEFAULT_STATUS_FILE,
) -> Path:
    status_map = load_connector_status(path)
    status_map[run_status.name] = asdict(run_status)
    return save_connector_status(status_map, path)


def summarize_connector_status(status_map: Dict[str, Any]) -> Dict[str, Any]:
    summary = {
        "total": len(status_map),
        "ok": 0,
        "empty": 0,
        "failed": 0,
        "semi_auto": 0,
        "skipped": 0,
        "needs_attention": [],
    }
    for name, status in status_map.items():
        state = status.get("status", "unknown")
        if state in summary:
            summary[state] += 1
        if state != "ok" or status.get("needs_cookie") or status.get("needs_payload"):
            summary["needs_attention"].append({
                "name": name,
                "city": status.get("city"),
                "status": state,
                "error": status.get("error"),
                "notes": status.get("notes"),
            })
    return summary


def render_connector_status_report(path: Path | str = DEFAULT_STATUS_FILE) -> str:
    status_map = load_connector_status(path)
    summary = summarize_connector_status(status_map)
    lines = ["Connector status", "=" * 20]
    lines.append(f"total: {summary['total']}")
    lines.append(f"ok: {summary['ok']}")
    lines.append(f"empty: {summary['empty']}")
    lines.append(f"failed: {summary['failed']}")
    lines.append(f"semi_auto: {summary['semi_auto']}")
    lines.append(f"skipped: {summary['skipped']}")
    if summary["needs_attention"]:
        lines.append("\nNeeds attention:")
        for item in summary["needs_attention"]:
            lines.append(f"- {item['name']} ({item.get('city')}): {item.get('status')} {item.get('error') or ''} {item.get('notes') or ''}")
    return "\n".join(lines)
