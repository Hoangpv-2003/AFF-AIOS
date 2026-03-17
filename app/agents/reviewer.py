"""Reviewer agent implementation for static checks and verdict emission."""

from __future__ import annotations

from typing import Dict

from app.agents.base_agent import AgentContext, AgentResult, BaseAgent
from app.schemas.agents import CoderArtifactDraft, ReviewStatus, ReviewVerdictDraft


class ReviewerAgent(BaseAgent):
	name = "reviewer"

	def review_artifacts(self, artifacts: CoderArtifactDraft) -> ReviewVerdictDraft:
		if not artifacts.files:
			return ReviewVerdictDraft(
				status=ReviewStatus.warn,
				reason_code="VALIDATION_FAILED",
				notes="No files generated",
			)
		if "unsafe" in artifacts.rationale.lower():
			return ReviewVerdictDraft(
				status=ReviewStatus.fail,
				reason_code="SANDBOX_DENIED",
				notes="Unsafe patterns detected",
			)
		return ReviewVerdictDraft(status=ReviewStatus.pass_)

	def act(self, context: AgentContext, inputs: Dict[str, object]) -> AgentResult:
		artifacts_data = inputs.get("artifacts")
		if not isinstance(artifacts_data, dict):
			return AgentResult(success=False, reason_code="VALIDATION_FAILED")
		artifacts = CoderArtifactDraft(**artifacts_data)
		verdict = self.review_artifacts(artifacts)
		return AgentResult(success=True, payload={"verdict": verdict.model_dump()})

