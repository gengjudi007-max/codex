from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from codex.services.queue_runtime import LocalPriorityQueue, QueueEvent


class BaseWorker:
    worker_type = "base"

    def process(self, event: QueueEvent) -> Dict[str, Any]:
        return {
            "worker_type": self.worker_type,
            "event_type": event.event_type,
            "status": "processed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


class ConnectorWorker(BaseWorker):
    worker_type = "connector"


class OCRWorker(BaseWorker):
    worker_type = "ocr"


class IntelligenceWorker(BaseWorker):
    worker_type = "intelligence"


class PublishingWorker(BaseWorker):
    worker_type = "publishing"


class WorkerRuntime:
    def __init__(self, queue_runtime: LocalPriorityQueue | None = None) -> None:
        self.queue_runtime = queue_runtime or LocalPriorityQueue()
        self.workers = {
            "connector.poll": ConnectorWorker(),
            "ocr.process": OCRWorker(),
            "intelligence.run": IntelligenceWorker(),
            "publishing.package": PublishingWorker(),
        }

    def run_once(self) -> Dict[str, Any]:
        processed: List[Dict[str, Any]] = []

        while self.queue_runtime.size() > 0:
            event = self.queue_runtime.consume()
            if not event:
                break
            worker = self.workers.get(event.event_type, BaseWorker())
            result = worker.process(event)
            processed.append(result)
            self.queue_runtime.task_done()

        return {
            "mode": "worker_runtime",
            "processed": processed,
            "processed_count": len(processed),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
