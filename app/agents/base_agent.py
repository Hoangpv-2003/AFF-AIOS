"""Base agent contracts shared by planner/coder/reviewer/manager."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


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


@dataclass
class AgentResult:
    success: bool
    payload: Optional[Dict[str, Any]] = None
    reason_code: Optional[str] = None
    notes: Optional[str] = None


class BaseAgent(abc.ABC):
    """Abstract base class with structured think/act/observe lifecycle."""

    name: str = "base"

    def think(self, context: AgentContext) -> AgentResult:
        return AgentResult(
            success=True,
            payload={"step": AgentStep.THINK.value},
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
        return AgentResult(
            success=result.success,
            payload={"step": AgentStep.OBSERVE.value},
            reason_code=result.reason_code,
            notes=result.notes,
        )
