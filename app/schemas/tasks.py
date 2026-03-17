"""Task draft schemas."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TaskPriority(str, Enum):
    interactive = "interactive"
    standard = "standard"
    batch = "batch"


class TaskState(str, Enum):
    received = "RECEIVED"
    planned = "PLANNED"
    coded = "CODED"
    reviewed_pass = "REVIEWED_PASS"
    reviewed_warn = "REVIEWED_WARN"
    waiting_approval = "WAITING_APPROVAL"
    approved = "APPROVED"
    activated = "ACTIVATED"
    failed = "FAILED"
    cancelled = "CANCELLED"


class TaskCreateDraft(BaseModel):
    prompt: str = Field(min_length=1)
    priority: TaskPriority = TaskPriority.standard


class TaskStatusDraft(BaseModel):
    task_id: str
    state: TaskState
    reason_code: Optional[str] = None
