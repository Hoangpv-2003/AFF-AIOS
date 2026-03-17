"""Local Redis/RQ-like queue adapter used for Phase 2C tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from app.infrastructure.queue.queue_client import QueueJob


@dataclass
class _Counter:
    value: int = 0


class RedisRQQueueClient:
    def __init__(self) -> None:
        self._counter = _Counter()
        self._jobs: Dict[str, QueueJob] = {}
        self._depth: Dict[str, int] = {
            "interactive": 0,
            "standard": 0,
            "batch": 0,
        }

    def submit(self, priority: str, payload: Dict[str, str]) -> QueueJob:
        self._counter.value += 1
        job_id = f"job-{self._counter.value}"
        job = QueueJob(job_id=job_id, priority=priority, payload=payload)
        self._jobs[job_id] = job
        self._depth[priority] = self._depth.get(priority, 0) + 1
        return job

    def cancel(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job is None:
            return False
        if job.status == "cancelled":
            return True
        job.status = "cancelled"
        self._depth[job.priority] = max(
            0,
            self._depth.get(job.priority, 0) - 1,
        )
        return True

    def get_status(self, job_id: str) -> str:
        job = self._jobs.get(job_id)
        return job.status if job else "missing"

    def queue_depth(self, priority: str) -> int:
        return self._depth.get(priority, 0)

    def set_depth(self, priority: str, value: int) -> None:
        self._depth[priority] = max(0, value)

    def metrics(self) -> Dict[str, int]:
        return {
            "queued_interactive": self._depth.get("interactive", 0),
            "queued_standard": self._depth.get("standard", 0),
            "queued_batch": self._depth.get("batch", 0),
            "total_jobs": len(self._jobs),
        }
