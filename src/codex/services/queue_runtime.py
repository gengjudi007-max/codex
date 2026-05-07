from __future__ import annotations

import json
import queue
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_QUEUE_LOG = "data/run_logs/queue_runtime.jsonl"


@dataclass
class QueueEvent:
    event_type: str
    payload: Dict[str, Any]
    priority: int = 5
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class LocalPriorityQueue:
    """Local queue abstraction used as a fallback before Redis/Kafka integration."""

    def __init__(self, log_path: str = DEFAULT_QUEUE_LOG) -> None:
        self._queue: queue.PriorityQueue[tuple[int, float, QueueEvent]] = queue.PriorityQueue()
        self.log_path = log_path

    def publish(self, event: QueueEvent) -> Dict[str, Any]:
        self._queue.put((event.priority, time.time(), event))
        self._log("published", event)
        return {"status": "published", "event": asdict(event), "queue_size": self._queue.qsize()}

    def consume(self) -> QueueEvent | None:
        if self._queue.empty():
            return None
        _, _, event = self._queue.get()
        self._log("consumed", event)
        return event

    def task_done(self) -> None:
        self._queue.task_done()

    def size(self) -> int:
        return self._queue.qsize()

    def drain(self) -> List[QueueEvent]:
        events = []
        while not self._queue.empty():
            event = self.consume()
            if event:
                events.append(event)
        return events

    def _log(self, action: str, event: QueueEvent) -> None:
        path = Path(self.log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {"ts": datetime.now(timezone.utc).isoformat(), "action": action, "event": asdict(event)}
        path.open("a", encoding="utf-8").write(json.dumps(record, ensure_ascii=False) + "\n")


def build_event(event_type: str, payload: Dict[str, Any] | None = None, priority: int = 5) -> QueueEvent:
    return QueueEvent(event_type=event_type, payload=payload or {}, priority=priority)
