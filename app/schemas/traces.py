from __future__ import annotations

"""Trace schemas."""

from typing import Optional

from pydantic import BaseModel


class TraceEvent(BaseModel):
    trace_id: str
    step: str
    message: str


class TraceQuery(BaseModel):
    task_id: Optional[str] = None
    trace_id: Optional[str] = None
    skill_id: Optional[str] = None
