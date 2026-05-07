from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List

from codex.services.queue_runtime import LocalPriorityQueue, build_event


class ConnectorScheduler:
    """Lightweight scheduler before distributed runtime deployment."""

    def __init__(self, queue_runtime: LocalPriorityQueue | None = None) -> None:
        self.queue_runtime = queue_runtime or LocalPriorityQueue()
        self.connectors: List[Dict[str, Any]] = []

    def register_connector(
        self,
        name: str,
        cadence_seconds: int,
        priority: int = 5,
        enabled: bool = True,
    ) -> Dict[str, Any]:
        connector = {
            "name": name,
            "cadence_seconds": cadence_seconds,
            "priority": priority,
            "enabled": enabled,
            "last_run": None,
        }
        self.connectors.append(connector)
        return connector

    def run_once(self) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        scheduled = []

        for connector in self.connectors:
            if not connector["enabled"]:
                continue
            event = build_event(
                event_type="connector.poll",
                payload={"connector": connector["name"], "scheduled_at": now},
                priority=connector["priority"],
            )
            self.queue_runtime.publish(event)
            connector["last_run"] = now
            scheduled.append(connector["name"])

        return {
            "mode": "connector_scheduler",
            "scheduled_connectors": scheduled,
            "queue_size": self.queue_runtime.size(),
            "timestamp": now,
        }

    def loop(self, iterations: int = 1) -> List[Dict[str, Any]]:
        snapshots = []
        for _ in range(iterations):
            snapshots.append(self.run_once())
            time.sleep(1)
        return snapshots
