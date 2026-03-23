"""Manager orchestrator with explicit state machine for agent flow."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from app.agents.base_agent import AgentContext
from app.agents.coder import CoderAgent
from app.agents.reviewer import ReviewerAgent
from app.brain.planner import PlannerAgent
from app.core.constants import ADMISSION_DEPTH_THRESHOLDS
from app.core.constants import ADMISSION_REASON_CODES
from app.core.constants import QUEUE_CLASSES
from app.infrastructure.queue.redis_rq_client import RedisRQQueueClient


@dataclass
class ManagerRunResult:
    task_id: str
    final_state: str
    transitions: List[str] = field(default_factory=list)
    reason_code: Optional[str] = None
    execution_log: List[Dict[str, object]] = field(default_factory=list)


class ManagerAgent:
    VALID_TRANSITIONS = {
        "RECEIVED": {"INTENT_PARSED", "FAILED", "CANCELLED"},
        "INTENT_PARSED": {"PLANNED", "FAILED", "CANCELLED"},
        "PLANNED": {"ROUTED", "FAILED", "CANCELLED"},
        "ROUTED": {"CODED", "FAILED", "CANCELLED"},
        "CODED": {"REVIEWED_PASS", "REVIEWED_WARN", "FAILED", "CANCELLED"},
        "REVIEWED_PASS": {"WAITING_APPROVAL", "FAILED", "CANCELLED"},
        "REVIEWED_WARN": {"CODED", "WAITING_APPROVAL", "FAILED", "CANCELLED"},
        "WAITING_APPROVAL": {"APPROVED", "FAILED", "CANCELLED"},
        "APPROVED": {"EXECUTED", "FAILED", "CANCELLED"},
        "EXECUTED": {"VALIDATED", "FAILED", "CANCELLED"},
        "VALIDATED": {"FINISHED", "FAILED", "CANCELLED"},
        "FINISHED": set(),
        "FAILED": set(),
        "CANCELLED": set(),
    }

    def __init__(
        self,
        intent_parser: Optional[Any] = None,  # Placeholder for new agents
        planner: Optional[PlannerAgent] = None,
        router: Optional[Any] = None,
        coder: Optional[CoderAgent] = None,
        reviewer: Optional[ReviewerAgent] = None,
        validator: Optional[Any] = None,
        queue_client: Optional[RedisRQQueueClient] = None,
        history_manager: Optional[Any] = None,
        retry_on_warn: bool = True,
        max_warn_retries: int = 1,
    ) -> None:
        self.planner = planner or PlannerAgent()
        self.coder = coder or CoderAgent()
        self.reviewer = reviewer or ReviewerAgent()
        self.queue_client = queue_client or RedisRQQueueClient()
        self.retry_on_warn = retry_on_warn
        self.max_warn_retries = max(0, int(max_warn_retries))
        self._provider_failures = 0

    def transition(self, current: str, next_state: str) -> str:
        allowed = self.VALID_TRANSITIONS.get(current, set())
        if next_state not in allowed:
            raise ValueError(f"Illegal transition: {current} -> {next_state}")
        return next_state

    def evaluate_admission(self, priority: str) -> Tuple[bool, str]:
        if priority not in QUEUE_CLASSES:
            return False, ADMISSION_REASON_CODES["invalid_priority"]

        depth = self.queue_client.queue_depth(priority)
        threshold = ADMISSION_DEPTH_THRESHOLDS.get(priority, 0)
        if depth > threshold:
            return False, ADMISSION_REASON_CODES["queue_overloaded"]
        return True, ADMISSION_REASON_CODES["accepted"]

    def _forced_terminal_state(
        self,
        state: str,
        *,
        cancel_at_state: Optional[str],
        fail_at_state: Optional[str],
    ) -> Tuple[Optional[str], Optional[str]]:
        if cancel_at_state and state == cancel_at_state:
            return "CANCELLED", "USER_CANCELLED"
        if fail_at_state and state == fail_at_state:
            return "FAILED", "TIMEOUT"
        return None, None

    def _normalize_reviewer_outcome(
        self,
        review_payload: Dict[str, Any],
    ) -> Tuple[str, Optional[str]]:
        verdict = review_payload.get("verdict")
        if not isinstance(verdict, dict):
            verdict = review_payload

        raw_status = verdict.get("status", "")
        if hasattr(raw_status, "value"):
            status = str(getattr(raw_status, "value")).strip().lower()
        else:
            status = str(raw_status).strip().lower()
        reason_code = verdict.get("reason_code")
        if reason_code is not None:
            reason_code = str(reason_code)

        if status == "pass":
            return "pass", None
        if status == "warn":
            return "warn", reason_code or "VALIDATION_FAILED"
        if status == "fail":
            return "fail", reason_code or "VALIDATION_FAILED"

        # Backward-compatible verdict format used by reviewer.review_artifacts
        if bool(verdict.get("is_approved")):
            return "pass", None
        return "warn", reason_code or "VALIDATION_FAILED"

    def run(
        self,
        task_id: str,
        prompt: str,
        priority: str = "standard",
        context_data: Optional[Dict] = None,
        cancel_at_state: Optional[str] = None,
        fail_at_state: Optional[str] = None,
    ) -> ManagerRunResult:
        transitions: List[str] = []
        execution_log: List[Dict[str, object]] = []
        state = "RECEIVED"
        transitions.append(state)
        reason_code: Optional[str] = None

        def move(next_state: str) -> str:
            nonlocal state
            state = self.transition(state, next_state)
            transitions.append(state)
            return state

        accepted, admission_reason = self.evaluate_admission(priority)
        if not accepted:
            move("FAILED")
            return ManagerRunResult(
                task_id=task_id,
                final_state=state,
                transitions=transitions,
                reason_code=admission_reason,
                execution_log=execution_log,
            )

        try:
            for next_state in ("INTENT_PARSED", "PLANNED", "ROUTED"):
                move(next_state)
                terminal_state, terminal_reason = self._forced_terminal_state(
                    state,
                    cancel_at_state=cancel_at_state,
                    fail_at_state=fail_at_state,
                )
                if terminal_state:
                    move(terminal_state)
                    reason_code = terminal_reason
                    return ManagerRunResult(
                        task_id=task_id,
                        final_state=state,
                        transitions=transitions,
                        reason_code=reason_code,
                        execution_log=execution_log,
                    )

            warn_retries_used = 0
            while True:
                move("CODED")
                terminal_state, terminal_reason = self._forced_terminal_state(
                    state,
                    cancel_at_state=cancel_at_state,
                    fail_at_state=fail_at_state,
                )
                if terminal_state:
                    move(terminal_state)
                    reason_code = terminal_reason
                    break

                review_context = AgentContext(
                    task_id=task_id,
                    trace_id=f"trace-{task_id}",
                    prompt=prompt,
                    priority=priority,
                    metadata=context_data or {},
                )
                review_inputs = {
                    "code_text": (
                        "def run(input_data=None, **kwargs):\n"
                        "    return {'status': 'success'}\n"
                    ),
                    "iteration": warn_retries_used + 1,
                }
                review_result = self.reviewer.act(
                    review_context,
                    review_inputs,
                )

                if not review_result.success:
                    move("REVIEWED_WARN")
                    reason_code = review_result.reason_code or "PROVIDER_ERROR"
                    move("WAITING_APPROVAL")
                    break

                review_status, review_reason = (
                    self._normalize_reviewer_outcome(
                        review_result.payload or {}
                    )
                )
                if review_status == "pass":
                    move("REVIEWED_PASS")
                    move("WAITING_APPROVAL")
                    break

                if review_status == "fail":
                    reason_code = review_reason or "VALIDATION_FAILED"
                    move("FAILED")
                    break

                move("REVIEWED_WARN")
                reason_code = review_reason or "VALIDATION_FAILED"
                if (
                    self.retry_on_warn
                    and warn_retries_used < self.max_warn_retries
                ):
                    warn_retries_used += 1
                    execution_log.append(
                        {
                            "event": "retry_on_warn",
                            "attempt": warn_retries_used,
                            "reason_code": reason_code,
                        }
                    )
                    continue

                move("WAITING_APPROVAL")
                break

        except Exception as e:
            execution_log.append({"error": str(e)})
            state = "FAILED"
            transitions.append(state)
            reason_code = reason_code or "VALIDATION_FAILED"

        return ManagerRunResult(
            task_id=task_id,
            final_state=state,
            transitions=transitions,
            reason_code=reason_code,
            execution_log=execution_log,
        )
