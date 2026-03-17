"""Queue client interface for manager orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Protocol


@dataclass
class QueueJob:
    job_id: str
    priority: str
    payload: Dict[str, str]
    status: str = "queued"


class QueueClient(Protocol):
    def submit(self, priority: str, payload: Dict[str, str]) -> QueueJob:
        ...

    def cancel(self, job_id: str) -> bool:
        ...

    def get_status(self, job_id: str) -> str:
        ...

    def queue_depth(self, priority: str) -> int:
        ...

    def metrics(self) -> Dict[str, int]:
        ...
