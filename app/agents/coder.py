"""Coder agent implementation for generating draft artifacts from plan."""

from __future__ import annotations

from typing import Dict, List, Optional

from app.agents.base_agent import AgentContext, AgentResult, BaseAgent
from app.schemas.agents import CoderArtifactDraft, PlanDraft


class CoderAgent(BaseAgent):
    name = "coder"

    def generate_artifacts(
        self,
        plan: PlanDraft,
        memory_hits: Optional[List[Dict[str, str]]] = None,
    ) -> CoderArtifactDraft:
        slug = plan.objective.lower().replace(" ", "_")
        files = [
            f"skills/dynamic/{slug}.py",
            f"tests/generated/test_{slug}.py",
        ]
        rationale = (
            f"Generated from plan with {len(plan.steps)} step(s)."
            f" memory_hits={len(memory_hits or [])}"
        )
        return CoderArtifactDraft(files=files, rationale=rationale)

    def act(
        self,
        context: AgentContext,
        inputs: Dict[str, object],
    ) -> AgentResult:
        plan_data = inputs.get("plan")
        if not isinstance(plan_data, dict):
            return AgentResult(success=False, reason_code="VALIDATION_FAILED")

        plan = PlanDraft(**plan_data)
        artifacts = self.generate_artifacts(
            plan=plan,
            memory_hits=inputs.get("memory_hits"),
        )
        return AgentResult(
            success=True,
            payload={"artifacts": artifacts.model_dump()},
        )
