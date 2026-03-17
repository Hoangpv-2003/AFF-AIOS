from __future__ import annotations

"""Trace endpoints."""

from typing import Optional

from fastapi import APIRouter

from app.schemas.traces import TraceEvent
from app.infrastructure.observability.tracing import get_tracer

router = APIRouter()
tracer = get_tracer()


@router.get("")
async def list_traces(task_id: Optional[str] = None, trace_id: Optional[str] = None):
    if trace_id is None:
        return {"task_id": task_id, "trace_id": trace_id, "events": []}
    return {
        "task_id": task_id,
        "trace_id": trace_id,
        "events": tracer.get_trace_chain(trace_id),
    }


@router.get("/{trace_id}", response_model=TraceEvent)
async def get_trace(trace_id: str):
    events = tracer.get_trace_events(trace_id)
    if events:
        event = events[0]
        return TraceEvent(trace_id=event.trace_id, step=event.name, message=event.message)
    return TraceEvent(trace_id=trace_id, step="root", message="trace placeholder")
