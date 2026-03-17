from __future__ import annotations

"""Task endpoints with stable schema and draft compatibility."""

from typing import Optional, Union

from fastapi import APIRouter, Header, HTTPException, Response

from app.schemas.tasks import TaskCreate, TaskCreateDraft, TaskState, TaskStatus

router = APIRouter()
_TASKS: dict[str, TaskStatus] = {}
_IDEMPOTENCY: dict[str, str] = {}

_DRAFT_SCHEMA_TOKEN = "draft"
_DEPRECATION_HEADER_VALUE = "true"
_SUNSET_HEADER_VALUE = "Wed, 30 Sep 2026 00:00:00 GMT"


def _apply_draft_deprecation_headers(response: Response) -> None:
    response.headers["Deprecation"] = _DEPRECATION_HEADER_VALUE
    response.headers["Sunset"] = _SUNSET_HEADER_VALUE
    response.headers["X-AAF-Migration"] = "draft->stable"


def _to_task_create(payload: TaskCreate | TaskCreateDraft) -> TaskCreate:
    return TaskCreate(prompt=payload.prompt, priority=payload.priority)


@router.post("", response_model=TaskStatus)
async def create_task(
    payload: Union[TaskCreate, TaskCreateDraft],
    response: Response,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    schema_mode: Optional[str] = Header(default=None, alias="X-AAF-Schema"),
):
    _to_task_create(payload)
    if schema_mode == _DRAFT_SCHEMA_TOKEN:
        _apply_draft_deprecation_headers(response)

    if idempotency_key and idempotency_key in _IDEMPOTENCY:
        return _TASKS[_IDEMPOTENCY[idempotency_key]]

    task_id = f"task-{len(_TASKS) + 1}"
    status = TaskStatus(task_id=task_id, state=TaskState.received)
    _TASKS[task_id] = status
    if idempotency_key:
        _IDEMPOTENCY[idempotency_key] = task_id
    return status


@router.get("", response_model=list[TaskStatus])
async def list_tasks():
    return list(_TASKS.values())


@router.get("/{task_id}", response_model=TaskStatus)
async def get_task(task_id: str):
    if task_id not in _TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    return _TASKS[task_id]


@router.post("/{task_id}/cancel", response_model=TaskStatus)
async def cancel_task(task_id: str):
    if task_id not in _TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    _TASKS[task_id] = TaskStatus(task_id=task_id, state=TaskState.cancelled, reason_code="USER_CANCELLED")
    return _TASKS[task_id]
