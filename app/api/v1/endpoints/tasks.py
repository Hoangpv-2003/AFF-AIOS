from __future__ import annotations

"""Task endpoints."""

from typing import Optional

from fastapi import APIRouter, Header, HTTPException

from app.schemas.tasks import TaskCreateDraft, TaskStatusDraft, TaskState

router = APIRouter()
_TASKS: dict[str, TaskStatusDraft] = {}
_IDEMPOTENCY: dict[str, str] = {}


@router.post("", response_model=TaskStatusDraft)
async def create_task(payload: TaskCreateDraft, idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key")):
    if idempotency_key and idempotency_key in _IDEMPOTENCY:
        return _TASKS[_IDEMPOTENCY[idempotency_key]]

    task_id = f"task-{len(_TASKS) + 1}"
    status = TaskStatusDraft(task_id=task_id, state=TaskState.received)
    _TASKS[task_id] = status
    if idempotency_key:
        _IDEMPOTENCY[idempotency_key] = task_id
    return status


@router.get("", response_model=list[TaskStatusDraft])
async def list_tasks():
    return list(_TASKS.values())


@router.get("/{task_id}", response_model=TaskStatusDraft)
async def get_task(task_id: str):
    if task_id not in _TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    return _TASKS[task_id]


@router.post("/{task_id}/cancel", response_model=TaskStatusDraft)
async def cancel_task(task_id: str):
    if task_id not in _TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    current = _TASKS[task_id]
    _TASKS[task_id] = TaskStatusDraft(task_id=task_id, state=TaskState.cancelled, reason_code="USER_CANCELLED")
    return _TASKS[task_id]
