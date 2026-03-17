"""Prompt-level tracing wrapper with correlation helpers."""

from __future__ import annotations

from typing import Dict, Optional

from app.infrastructure.observability.tracing import get_tracer


def trace_prompt_call(
    trace_id: str,
    prompt_name: str,
    prompt_text: str,
    parent_span_id: Optional[str] = None,
    metadata: Optional[Dict[str, object]] = None,
) -> str:
    tracer = get_tracer()
    span_id = tracer.start_span(
        trace_id=trace_id,
        name=f"prompt.{prompt_name}",
        parent_span_id=parent_span_id,
        kind="prompt",
        attributes={
            "prompt_length": len(prompt_text),
            **(metadata or {}),
        },
    )
    tracer.add_event(
        trace_id=trace_id,
        span_id=span_id,
        name="prompt.executed",
        message="Prompt execution traced",
        attributes={"prompt_preview": prompt_text[:80]},
    )
    tracer.end_span(span_id, status="ok")
    return span_id


def correlation_fields(trace_id: str, span_id: str, parent_span_id: Optional[str] = None) -> Dict[str, Optional[str]]:
    return {
        "trace_id": trace_id,
        "span_id": span_id,
        "parent_span_id": parent_span_id,
    }
