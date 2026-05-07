from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, TypeVar

T = TypeVar("T")
DEFAULT_EVENT_LOG = "data/run_logs/events.jsonl"
DEFAULT_CACHE_DIR = "data/cache"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_event(
    event_type: str,
    message: str,
    payload: Dict[str, Any] | None = None,
    level: str = "info",
    log_path: str = DEFAULT_EVENT_LOG,
) -> Dict[str, Any]:
    event = {
        "ts": now_iso(),
        "level": level,
        "event_type": event_type,
        "message": message,
        "payload": payload or {},
    }
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def safe_step(
    name: str,
    fn: Callable[[], T],
    log_path: str = DEFAULT_EVENT_LOG,
) -> Dict[str, Any]:
    started = time.time()
    try:
        result = fn()
        elapsed_ms = int((time.time() - started) * 1000)
        log_event(name, "step completed", {"elapsed_ms": elapsed_ms}, "info", log_path)
        return {"name": name, "status": "ok", "elapsed_ms": elapsed_ms, "result": result}
    except Exception as exc:  # noqa: BLE001
        elapsed_ms = int((time.time() - started) * 1000)
        log_event(name, "step failed", {"elapsed_ms": elapsed_ms, "error": str(exc)}, "error", log_path)
        return {"name": name, "status": "failed", "elapsed_ms": elapsed_ms, "error": str(exc), "result": None}


def retry(
    fn: Callable[[], T],
    attempts: int = 3,
    delay_seconds: float = 1.0,
) -> T:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < attempts:
                time.sleep(delay_seconds)
    if last_error:
        raise last_error
    raise RuntimeError("retry failed without exception")


def cache_get(key: str, cache_dir: str = DEFAULT_CACHE_DIR) -> Dict[str, Any] | None:
    path = _cache_path(key, cache_dir)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def cache_set(key: str, value: Dict[str, Any], cache_dir: str = DEFAULT_CACHE_DIR) -> Dict[str, Any]:
    path = _cache_path(key, cache_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"cached_at": now_iso(), "value": value}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def cache_key(*parts: Any) -> str:
    raw = "|".join(str(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def summarize_steps(steps: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    failed = [name for name, step in steps.items() if step.get("status") != "ok"]
    return {
        "overall_status": "failed" if failed else "ok",
        "failed_steps": failed,
        "step_count": len(steps),
        "ok_count": len(steps) - len(failed),
    }


def _cache_path(key: str, cache_dir: str) -> Path:
    safe_key = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return Path(cache_dir) / f"{safe_key}.json"
