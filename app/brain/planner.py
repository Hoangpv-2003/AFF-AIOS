"""Planner agent implementation for NL -> plan decomposition."""

from __future__ import annotations

from typing import Dict, List

from app.agents.base_agent import AgentContext, AgentResult, BaseAgent
from app.brain.reasoning import validate_non_empty
from app.infrastructure.budget.enforcer import BudgetEnforcer
from app.schemas.agents import PlanDraft


class PlannerAgent(BaseAgent):
	name = "planner"

	def __init__(self, budget_enforcer: BudgetEnforcer | None = None) -> None:
		self.budget_enforcer = budget_enforcer

	def create_plan(self, task_input: str) -> PlanDraft:
		validate_non_empty(task_input, "task_input")
		raw_steps = [step.strip() for step in task_input.split(".") if step.strip()]
		steps: List[str] = raw_steps if raw_steps else ["analyze task", "produce output"]
		confidence = 0.8 if len(steps) >= 2 else 0.6
		return PlanDraft(objective=task_input.strip(), steps=steps, confidence=confidence)

	def act(self, context: AgentContext, inputs: Dict[str, str]) -> AgentResult:
		prompt = inputs.get("prompt", context.prompt)
		if self.budget_enforcer is not None:
			user_id = str(context.metadata.get("user_id", "system"))
			org_id = str(context.metadata.get("org_id", "default"))
			tokens = self.budget_enforcer.estimate_tokens(prompt)
			allowed, reason = self.budget_enforcer.preflight(
				task_id=context.task_id,
				user_id=user_id,
				org_id=org_id,
				tokens=tokens,
			)
			if not allowed:
				return AgentResult(success=False, reason_code=reason)

		plan = self.create_plan(prompt)
		return AgentResult(success=True, payload={"plan": plan.model_dump()})

