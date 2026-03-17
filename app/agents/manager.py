"""Manager orchestrator with explicit state machine for agent flow."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from app.agents.base_agent import AgentContext
from app.agents.coder import CoderAgent
from app.agents.reviewer import ReviewerAgent
from app.brain.planner import PlannerAgent
from app.core.constants import ADMISSION_DEPTH_THRESHOLDS
from app.core.constants import ADMISSION_REASON_CODES
from app.core.constants import QUEUE_CLASSES, SLA_TARGET_MS
from app.infrastructure.queue.redis_rq_client import RedisRQQueueClient
from app.schemas.agents import ReviewStatus


@dataclass
class ManagerRunResult:
    task_id: str
    final_state: str
    transitions: List[str] = field(default_factory=list)
    reason_code: Optional[str] = None


class ManagerAgent:
    VALID_TRANSITIONS = {
        "RECEIVED": {"PLANNED", "FAILED", "CANCELLED"},
        "PLANNED": {"CODED", "FAILED", "CANCELLED"},
        "CODED": {"REVIEWED_PASS", "REVIEWED_WARN", "FAILED", "CANCELLED"},
        "REVIEWED_PASS": {"WAITING_APPROVAL", "FAILED", "CANCELLED"},
        "REVIEWED_WARN": {"CODED", "WAITING_APPROVAL", "FAILED", "CANCELLED"},
        "WAITING_APPROVAL": {"APPROVED", "FAILED", "CANCELLED"},
        "APPROVED": {"ACTIVATED", "FAILED", "CANCELLED"},
        "ACTIVATED": set(),
        "FAILED": set(),
        "CANCELLED": set(),
    }

    def __init__(
        self,
        planner: Optional[PlannerAgent] = None,
        coder: Optional[CoderAgent] = None,
        reviewer: Optional[ReviewerAgent] = None,
        queue_client: Optional[RedisRQQueueClient] = None,
        retry_on_warn: bool = True,
        max_warn_retries: int = 1,
        circuit_breaker_limit: int = 3,
    ) -> None:
        self.planner = planner or PlannerAgent()
        self.coder = coder or CoderAgent()
        self.reviewer = reviewer or ReviewerAgent()
        self.queue_client = queue_client or RedisRQQueueClient()
        self.retry_on_warn = retry_on_warn
        self.max_warn_retries = max_warn_retries
        self.circuit_breaker_limit = circuit_breaker_limit
        self._provider_failures = 0

    def route_priority(self, priority: str) -> str:
        if priority not in QUEUE_CLASSES:
            return "standard"
        return priority

    def evaluate_admission(self, priority: str) -> Tuple[bool, str]:
        routed = self.route_priority(priority)
        if routed not in QUEUE_CLASSES:
            return False, ADMISSION_REASON_CODES["invalid_priority"]
        depth = self.queue_client.queue_depth(routed)
        if depth > ADMISSION_DEPTH_THRESHOLDS[routed]:
            return False, ADMISSION_REASON_CODES["queue_overloaded"]
        return True, ADMISSION_REASON_CODES["accepted"]

    @staticmethod
    def _deadline_seconds(priority: str) -> int:
        target_ms = SLA_TARGET_MS.get(priority, SLA_TARGET_MS["standard"])
        # Keep conservative execution budget as 3x SLA for orchestration steps.
        return max(1, int((target_ms * 3) / 1000))

    def _before_provider_call(self) -> None:
        if self._provider_failures >= self.circuit_breaker_limit:
            raise RuntimeError("Circuit breaker open")

    def _on_provider_success(self) -> None:
        self._provider_failures = 0

    def _on_provider_failure(self) -> None:
        self._provider_failures += 1

    def transition(self, current: str, next_state: str) -> str:
        allowed = self.VALID_TRANSITIONS.get(current, set())
        if next_state not in allowed:
            raise ValueError(f"Illegal transition: {current} -> {next_state}")
        return next_state

    def run(
        self,
        task_id: str,
        prompt: str,
        priority: str = "standard",
        cancel_at_state: Optional[str] = None,
        fail_at_state: Optional[str] = None,
    ) -> ManagerRunResult:
        transitions: List[str] = []
        state = "RECEIVED"
        transitions.append(state)

        allowed, admission_code = self.evaluate_admission(priority)
        if not allowed:
            state = self.transition(state, "FAILED")
            transitions.append(state)
            return ManagerRunResult(
                task_id=task_id,
                final_state=state,
                transitions=transitions,
                reason_code=admission_code,
            )

        routed_priority = self.route_priority(priority)
        deadline_seconds = self._deadline_seconds(routed_priority)

        context = AgentContext(
            task_id=task_id,
            trace_id=f"trace-{task_id}",
            prompt=prompt,
            priority=routed_priority,
            metadata={
                "deadline_at": time.time() + deadline_seconds,
                "admission_code": admission_code,
            },
        )

        def check_interrupt(next_state: str) -> Optional[ManagerRunResult]:
            nonlocal state
            if cancel_at_state == next_state:
                state = self.transition(state, "CANCELLED")
                transitions.append(state)
                return ManagerRunResult(
                    task_id=task_id,
                    final_state=state,
                    transitions=transitions,
                    reason_code="USER_CANCELLED",
                )
            if fail_at_state == next_state:
                state = self.transition(state, "FAILED")
                transitions.append(state)
                return ManagerRunResult(
                    task_id=task_id,
                    final_state=state,
                    transitions=transitions,
                    reason_code="TIMEOUT",
                )
            return None

        interrupted = check_interrupt("PLANNED")
        if interrupted:
            return interrupted
        state = self.transition(state, "PLANNED")
        transitions.append(state)

        try:
            self._before_provider_call()
            plan_result = self.planner.act(context, {"prompt": prompt})
            self._on_provider_success()
        except RuntimeError:
            self._on_provider_failure()
            state = self.transition(state, "FAILED")
            transitions.append(state)
            return ManagerRunResult(
                task_id,
                state,
                transitions,
                "PROVIDER_ERROR",
            )

        if not plan_result.success:
            self._on_provider_failure()
            state = self.transition(state, "FAILED")
            transitions.append(state)
            return ManagerRunResult(
                task_id,
                state,
                transitions,
                plan_result.reason_code,
            )
        plan_payload = (plan_result.payload or {}).get("plan", {})

        warn_retries = 0
        while True:
            interrupted = check_interrupt("CODED")
            if interrupted:
                return interrupted
            state = self.transition(state, "CODED")
            transitions.append(state)

            code_result = self.coder.act(
                context,
                {"plan": plan_payload, "memory_hits": []},
            )
            if not code_result.success:
                self._on_provider_failure()
                state = self.transition(state, "FAILED")
                transitions.append(state)
                return ManagerRunResult(
                    task_id,
                    state,
                    transitions,
                    code_result.reason_code,
                )
            artifacts = (code_result.payload or {}).get("artifacts", {})

            review_result = self.reviewer.act(
                context,
                {"artifacts": artifacts},
            )
            if not review_result.success:
                self._on_provider_failure()
                state = self.transition(state, "FAILED")
                transitions.append(state)
                return ManagerRunResult(
                    task_id,
                    state,
                    transitions,
                    review_result.reason_code,
                )
            verdict = (review_result.payload or {}).get("verdict", {})
            status = verdict.get("status")
            reason = verdict.get("reason_code")

            if status == ReviewStatus.pass_.value:
                self._on_provider_success()
                state = self.transition(state, "REVIEWED_PASS")
                transitions.append(state)
                state = self.transition(state, "WAITING_APPROVAL")
                transitions.append(state)
                return ManagerRunResult(task_id, state, transitions)

            if status == ReviewStatus.warn.value:
                state = self.transition(state, "REVIEWED_WARN")
                transitions.append(state)
                if self.retry_on_warn and warn_retries < self.max_warn_retries:
                    warn_retries += 1
                    continue
                state = self.transition(state, "WAITING_APPROVAL")
                transitions.append(state)
                return ManagerRunResult(
                    task_id=task_id,
                    final_state=state,
                    transitions=transitions,
                    reason_code=reason or "VALIDATION_FAILED",
                )

            state = self.transition(state, "FAILED")
            transitions.append(state)
            return ManagerRunResult(
                task_id=task_id,
                final_state=state,
                transitions=transitions,
                reason_code=reason or "VALIDATION_FAILED",
            )
