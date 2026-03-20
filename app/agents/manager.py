"""Manager orchestrator with explicit state machine for agent flow."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

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
    execution_log: List[Dict[str, object]] = field(default_factory=list)


class ManagerAgent:
    VALID_TRANSITIONS = {
        "RECEIVED": {"INTENT_PARSED", "FAILED", "CANCELLED"},
        "INTENT_PARSED": {"CLARIFIED", "PLANNED", "FAILED", "CANCELLED"},
        "CLARIFIED": {"INTENT_PARSED", "FAILED", "CANCELLED"},
        "PLANNED": {"ROUTED", "FAILED", "CANCELLED"},
        "ROUTED": {"CODED", "EXECUTED", "FAILED", "CANCELLED"},
        "CODED": {"REVIEWED", "FAILED", "CANCELLED"},
        "REVIEWED": {"EXECUTED", "CODED", "FAILED", "CANCELLED"},
        "EXECUTED": {"VALIDATED", "FAILED", "CANCELLED"},
        "VALIDATED": {"FINISHED", "PLANNED", "FAILED", "CANCELLED"},
        "FINISHED": set(),
        "FAILED": set(),
        "CANCELLED": set(),
    }

    def __init__(
        self,
        intent_parser: Optional[Any] = None, # Placeholder for new agents
        planner: Optional[PlannerAgent] = None,
        router: Optional[Any] = None,
        coder: Optional[CoderAgent] = None,
        reviewer: Optional[ReviewerAgent] = None,
        validator: Optional[Any] = None,
        queue_client: Optional[RedisRQQueueClient] = None,
        history_manager: Optional[Any] = None,
    ) -> None:
        self.planner = planner or PlannerAgent()
        self.coder = coder or CoderAgent()
        self.reviewer = reviewer or ReviewerAgent()
        self.queue_client = queue_client or RedisRQQueueClient()
        self._provider_failures = 0

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
        context_data: Optional[Dict] = None,
    ) -> ManagerRunResult:
        """
        Executes the full pipeline with state tracking.
        This is a high-level orchestrator similar to chat_agent but structured for state tracking.
        """
        transitions: List[str] = []
        execution_log: List[Dict[str, object]] = []
        state = "RECEIVED"
        transitions.append(state)
        
        # Simplified logic for demonstration of state machine compliance
        # In a real implementation, we would call the agent.act() methods for each stage.
        
        try:
            # 1. Intent Phase
            state = self.transition(state, "INTENT_PARSED")
            transitions.append(state)
            
            # 2. Planning Phase
            state = self.transition(state, "PLANNED")
            transitions.append(state)
            
            # 3. Routing Phase
            state = self.transition(state, "ROUTED")
            transitions.append(state)
            
            # 4. Coding/Executing Path
            # If Coder is needed:
            state = self.transition(state, "CODED")
            transitions.append(state)
            state = self.transition(state, "REVIEWED")
            transitions.append(state)
            
            # 5. Execution Phase
            state = self.transition(state, "EXECUTED")
            transitions.append(state)
            
            # 6. Validation Phase
            state = self.transition(state, "VALIDATED")
            transitions.append(state)
            
            # 7. Finish
            state = self.transition(state, "FINISHED")
            transitions.append(state)
            
        except Exception as e:
            execution_log.append({"error": str(e)})
            state = "FAILED"
            transitions.append(state)

        return ManagerRunResult(
            task_id=task_id,
            final_state=state,
            transitions=transitions,
            execution_log=execution_log,
        )
