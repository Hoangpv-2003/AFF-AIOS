"""Base agent contracts shared by planner/coder/reviewer/manager."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

from app.infrastructure.observability.prompt_trace import trace_prompt_call
from app.infrastructure.observability.tracing import get_tracer


class AgentStep(str, Enum):
    THINK = "THINK"
    ACT = "ACT"
    OBSERVE = "OBSERVE"


@dataclass
class AgentContext:
    task_id: str
    trace_id: str
    prompt: str
    priority: str = "standard"
    attempt: int = 0
    max_retries: int = 1
    budget_tokens: int = 0
    cancelled: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    history_summary: str = ""


@dataclass
class AgentResult:
    success: bool
    payload: Optional[Dict[str, Any]] = None
    reason_code: Optional[str] = None
    notes: Optional[str] = None


class BaseAgent(abc.ABC):
    """Abstract base class with structured think/act/observe lifecycle."""

    name: str = "base"

    def _emit_step_span(
        self,
        context: AgentContext,
        step: AgentStep,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> str:
        tracer = get_tracer()
        span_id = tracer.start_span(
            trace_id=context.trace_id,
            name=f"agent.{self.name}.{step.value.lower()}",
            kind="internal",
            attributes={
                "task_id": context.task_id,
                "priority": context.priority,
                "attempt": context.attempt,
                **(attributes or {}),
            },
        )
        tracer.add_event(
            trace_id=context.trace_id,
            span_id=span_id,
            name="agent.step",
            message=f"{self.name} -> {step.value}",
        )
        tracer.end_span(span_id, status="ok")
        return span_id

    def think(self, context: AgentContext) -> AgentResult:
        span_id = self._emit_step_span(context, AgentStep.THINK)
        trace_prompt_call(
            trace_id=context.trace_id,
            prompt_name=f"{self.name}.think",
            prompt_text=context.prompt,
            parent_span_id=span_id,
            metadata={"task_id": context.task_id},
        )
        return AgentResult(
            success=True,
            payload={"step": AgentStep.THINK.value, "span_id": span_id},
        )

    @abc.abstractmethod
    def act(
        self,
        context: AgentContext,
        inputs: Dict[str, Any],
    ) -> AgentResult:
        ...

    def observe(
        self,
        context: AgentContext,
        result: AgentResult,
    ) -> AgentResult:
        span_id = self._emit_step_span(
            context,
            AgentStep.OBSERVE,
            attributes={"success": result.success, "reason_code": result.reason_code},
        )
        return AgentResult(
            success=result.success,
            payload={"step": AgentStep.OBSERVE.value, "span_id": span_id},
            reason_code=result.reason_code,
            notes=result.notes,
        )
