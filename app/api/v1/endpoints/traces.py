from __future__ import annotations

"""Trace endpoints."""

from typing import Optional

from fastapi import APIRouter

from app.schemas.traces import TraceEvent

router = APIRouter()


@router.get("")
async def list_traces(task_id: Optional[str] = None, trace_id: Optional[str] = None):
    return {"task_id": task_id, "trace_id": trace_id, "events": []}


@router.get("/{trace_id}", response_model=TraceEvent)
async def get_trace(trace_id: str):
    return TraceEvent(trace_id=trace_id, step="root", message="trace placeholder")
