"""In-memory tracing primitives with OTLP-style metadata."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from time import time
from typing import Dict, List, Optional


@dataclass
class SpanRecord:
    trace_id: str
    span_id: str
    name: str
    parent_span_id: Optional[str] = None
    kind: str = "internal"
    started_at: float = field(default_factory=time)
    ended_at: Optional[float] = None
    status: str = "in_progress"
    attributes: Dict[str, object] = field(default_factory=dict)


@dataclass
class TraceEventRecord:
    trace_id: str
    span_id: str
    name: str
    message: str
    created_at: float = field(default_factory=time)
    attributes: Dict[str, object] = field(default_factory=dict)


class InMemoryTracer:
    def __init__(self) -> None:
        self._spans: Dict[str, SpanRecord] = {}
        self._events: List[TraceEventRecord] = []
        self._config: Dict[str, object] = {
            "service_name": "aaf-aios",
            "otlp_endpoint": None,
            "enabled": True,
        }

    def configure(self, service_name: str, otlp_endpoint: Optional[str] = None, enabled: bool = True) -> None:
        self._config = {
            "service_name": service_name,
            "otlp_endpoint": otlp_endpoint,
            "enabled": enabled,
        }

    def get_config(self) -> Dict[str, object]:
        return dict(self._config)

    def start_span(
        self,
        trace_id: str,
        name: str,
        parent_span_id: Optional[str] = None,
        kind: str = "internal",
        attributes: Optional[Dict[str, object]] = None,
    ) -> str:
        if not self._config.get("enabled", True):
            return ""
        span_id = str(uuid.uuid4())
        self._spans[span_id] = SpanRecord(
            trace_id=trace_id,
            span_id=span_id,
            name=name,
            parent_span_id=parent_span_id,
            kind=kind,
            attributes=attributes or {},
        )
        return span_id

    def end_span(self, span_id: str, status: str = "ok", attributes: Optional[Dict[str, object]] = None) -> None:
        if not span_id:
            return
        span = self._spans.get(span_id)
        if span is None:
            return
        span.ended_at = time()
        span.status = status
        if attributes:
            span.attributes.update(attributes)

    def add_event(
        self,
        trace_id: str,
        span_id: str,
        name: str,
        message: str,
        attributes: Optional[Dict[str, object]] = None,
    ) -> None:
        if not self._config.get("enabled", True):
            return
        self._events.append(
            TraceEventRecord(
                trace_id=trace_id,
                span_id=span_id,
                name=name,
                message=message,
                attributes=attributes or {},
            )
        )

    def get_trace_chain(self, trace_id: str) -> List[Dict[str, object]]:
        spans = [asdict(span) for span in self._spans.values() if span.trace_id == trace_id]
        events = [asdict(event) for event in self._events if event.trace_id == trace_id]
        spans.sort(key=lambda item: item["started_at"])
        events.sort(key=lambda item: item["created_at"])
        return spans + events

    def get_trace_events(self, trace_id: str) -> List[TraceEventRecord]:
        return [event for event in self._events if event.trace_id == trace_id]

    def clear(self) -> None:
        self._spans = {}
        self._events = []


_tracer = InMemoryTracer()


def configure_tracer(service_name: str, otlp_endpoint: Optional[str] = None, enabled: bool = True) -> None:
    _tracer.configure(service_name=service_name, otlp_endpoint=otlp_endpoint, enabled=enabled)


def get_tracer() -> InMemoryTracer:
    return _tracer
