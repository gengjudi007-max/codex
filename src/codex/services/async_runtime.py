from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List

from codex.services.realtime_pipeline import run_realtime_pipeline
from codex.services.reliability import log_event

DEFAULT_RUNTIME_LOG = "data/run_logs/async_runtime.jsonl"


@dataclass
class NewsroomEvent:
    event_type: str
    payload: Dict[str, Any]
    priority: int = 5
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class WorkerResult:
    event_id: str
    event_type: str
    status: str
    elapsed_ms: int
    result: Dict[str, Any] | None = None
    error: str | None = None


class AsyncNewsroomRuntime:
    """Lightweight async runtime for newsroom pipelines.

    This is intentionally single-process and stdlib-only. It provides the event bus,
    worker model, and watchdog foundation before moving to Redis/Celery/Kafka.
    """

    def __init__(self, worker_count: int = 2, runtime_log: str = DEFAULT_RUNTIME_LOG) -> None:
        self.worker_count = worker_count
        self.runtime_log = runtime_log
        self.queue: asyncio.PriorityQueue[tuple[int, float, NewsroomEvent]] = asyncio.PriorityQueue()
        self.handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = {
            "realtime_pipeline": self._handle_realtime_pipeline,
            "heartbeat": self._handle_heartbeat,
        }
        self.results: List[WorkerResult] = []
        self.started_at: str | None = None
        self.stopped_at: str | None = None

    async def publish(self, event: NewsroomEvent) -> None:
        await self.queue.put((event.priority, time.time(), event))
        self._append_log({"type": "event_published", "event": asdict(event)})

    async def run_until_empty(self) -> Dict[str, Any]:
        self.started_at = datetime.now(timezone.utc).isoformat()
        workers = [asyncio.create_task(self._worker(f"worker-{i}")) for i in range(self.worker_count)]
        await self.queue.join()
        for worker in workers:
            worker.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
        self.stopped_at = datetime.now(timezone.utc).isoformat()
        return self.state_snapshot()

    async def _worker(self, worker_name: str) -> None:
        while True:
            _, _, event = await self.queue.get()
            started = time.time()
            try:
                handler = self.handlers.get(event.event_type)
                if not handler:
                    raise ValueError(f"unknown event_type: {event.event_type}")
                result = await handler(event.payload)
                elapsed_ms = int((time.time() - started) * 1000)
                worker_result = WorkerResult(
                    event_id=event.event_id,
                    event_type=event.event_type,
                    status="ok",
                    elapsed_ms=elapsed_ms,
                    result=result,
                )
                self.results.append(worker_result)
                self._append_log({"type": "event_completed", "worker": worker_name, "result": asdict(worker_result)})
            except Exception as exc:  # noqa: BLE001
                elapsed_ms = int((time.time() - started) * 1000)
                worker_result = WorkerResult(
                    event_id=event.event_id,
                    event_type=event.event_type,
                    status="failed",
                    elapsed_ms=elapsed_ms,
                    error=str(exc),
                )
                self.results.append(worker_result)
                self._append_log({"type": "event_failed", "worker": worker_name, "result": asdict(worker_result)})
            finally:
                self.queue.task_done()

    async def _handle_realtime_pipeline(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await asyncio.to_thread(run_realtime_pipeline, payload)

    async def _handle_heartbeat(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "ok", "payload": payload, "ts": datetime.now(timezone.utc).isoformat()}

    def state_snapshot(self) -> Dict[str, Any]:
        failed = [result for result in self.results if result.status != "ok"]
        return {
            "mode": "async_newsroom_runtime",
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
            "worker_count": self.worker_count,
            "processed_count": len(self.results),
            "failed_count": len(failed),
            "queue_size": self.queue.qsize(),
            "results": [asdict(result) for result in self.results],
            "overall_status": "failed" if failed else "ok",
        }

    def _append_log(self, event: Dict[str, Any]) -> None:
        path = Path(self.runtime_log)
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {"ts": datetime.now(timezone.utc).isoformat(), **event}
        path.open("a", encoding="utf-8").write(json.dumps(record, ensure_ascii=False) + "\n")


def run_async_runtime_once(
    events: List[Dict[str, Any]],
    worker_count: int = 2,
    runtime_log: str = DEFAULT_RUNTIME_LOG,
) -> Dict[str, Any]:
    async def _run() -> Dict[str, Any]:
        runtime = AsyncNewsroomRuntime(worker_count=worker_count, runtime_log=runtime_log)
        for event in events:
            await runtime.publish(
                NewsroomEvent(
                    event_type=str(event.get("event_type") or "heartbeat"),
                    payload=event.get("payload", {}) if isinstance(event.get("payload", {}), dict) else {},
                    priority=int(event.get("priority", 5)),
                )
            )
        return await runtime.run_until_empty()

    log_event("async_runtime", "runtime_once started", {"event_count": len(events)})
    result = asyncio.run(_run())
    log_event("async_runtime", "runtime_once finished", {"summary": {"processed": result.get("processed_count"), "failed": result.get("failed_count")}})
    return result


def build_realtime_event(config: Dict[str, Any], priority: int = 5) -> Dict[str, Any]:
    return {"event_type": "realtime_pipeline", "priority": priority, "payload": config}
