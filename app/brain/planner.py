"""Planner agent implementation for NL -> plan decomposition."""

from __future__ import annotations

from typing import Dict, List

from app.agents.base_agent import AgentContext, AgentResult, BaseAgent
from app.brain.reasoning import validate_non_empty
from app.schemas.agents import PlanDraft


class PlannerAgent(BaseAgent):
	name = "planner"

	def create_plan(self, task_input: str) -> PlanDraft:
		validate_non_empty(task_input, "task_input")
		raw_steps = [step.strip() for step in task_input.split(".") if step.strip()]
		steps: List[str] = raw_steps if raw_steps else ["analyze task", "produce output"]
		confidence = 0.8 if len(steps) >= 2 else 0.6
		return PlanDraft(objective=task_input.strip(), steps=steps, confidence=confidence)

	def act(self, context: AgentContext, inputs: Dict[str, str]) -> AgentResult:
		plan = self.create_plan(inputs.get("prompt", context.prompt))
		return AgentResult(success=True, payload={"plan": plan.model_dump()})

