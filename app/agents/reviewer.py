"""Reviewer agent implementation for static checks and verdict emission."""

from __future__ import annotations

from typing import Any, Dict

from app.agents.base_agent import AgentContext, AgentResult, BaseAgent
from app.infrastructure.sandboxes.models import SandboxRequest
from app.infrastructure.sandboxes.runner import LocalSandboxRunner
from app.schemas.agents import CoderArtifactDraft, ReviewStatus, ReviewVerdictDraft


class ReviewerAgent(BaseAgent):
    name = "reviewer"

    def __init__(
        self, 
        sandbox_runner: LocalSandboxRunner | None = None,
        llm_client: Any | None = None,
    ) -> None:
        self.sandbox_runner = sandbox_runner or LocalSandboxRunner()
        self.llm_client = llm_client

    def review_artifacts(
        self,
        artifacts: CoderArtifactDraft,
        plan_json: str = "",
        iteration: int = 1,
    ) -> ReviewVerdictDraft:
        if not artifacts.generated_code:
            joined = " ".join(artifacts.files) + " " + artifacts.rationale
            lowered = joined.lower()
            if "http" in lowered or "net" in lowered or "network" in lowered:
                sandbox = self.sandbox_runner.run(
                    SandboxRequest(
                        skill_id="offline-review-network",
                        command="python",
                        args=["-c", "print('network check')"],
                        requires_network=True,
                    )
                )
                return ReviewVerdictDraft(
                    status=ReviewStatus.fail,
                    reason_code="SANDBOX_DENIED",
                    notes=";".join(sandbox.policy_violations) or sandbox.stderr,
                )

            return ReviewVerdictDraft(status=ReviewStatus.pass_)

        # 1. Static Security Heuristics
        code = artifacts.generated_code.lower()
        if "os.system" in code or "subprocess.popen" in code:
            return ReviewVerdictDraft(
                status=ReviewStatus.fail,
                reason_code="VALIDATION_FAILED",
                notes="Phat hien lenh thuc thi he thong khong an toan.",
            )

        # 2. LLM Review (if client available)
        if self.llm_client:
            from app.brain.prompt_templates import build_coder_review_messages
            messages = build_coder_review_messages(plan_json, artifacts.generated_code, iteration)
            try:
                res = self.llm_client.generate(
                    prompt=messages[1]["content"],
                    system_prompt=messages[0]["content"]
                )
                import json
                parsed = json.loads(str(res))
                if bool(parsed.get("is_approved", False)):
                    return ReviewVerdictDraft(status=ReviewStatus.pass_)
                return ReviewVerdictDraft(
                    status=ReviewStatus.warn,
                    reason_code=str(parsed.get("reason_code") or "VALIDATION_FAILED"),
                    notes=str(parsed.get("review_feedback") or ""),
                )
            except Exception:
                pass # Fallback to sandbox only

        # 3. Sandbox Execution (Logical verification)
        # For now, we use LocalSandboxRunner to check if it's runnable
        result = self.sandbox_runner.run(
            SandboxRequest(
                skill_id="codegen_review",
                command="python",
                args=["-c", artifacts.generated_code], # Try to compile/run
            )
        )
        if not result.success:
            return ReviewVerdictDraft(
                status=ReviewStatus.fail,
                reason_code="SANDBOX_DENIED",
                notes=(";".join(result.policy_violations) or result.stderr),
            )

        return ReviewVerdictDraft(status=ReviewStatus.pass_)

    def act(self, context: AgentContext, inputs: Dict[str, object]) -> AgentResult:
        artifacts_data = inputs.get("artifacts")
        if not artifacts_data and inputs.get("code_text"):
             # Support internal direct call from CoderAgent
             artifacts = CoderArtifactDraft(
                 files=[], 
                 rationale="", 
                 generated_code=str(inputs.get("code_text"))
             )
        elif isinstance(artifacts_data, dict):
            artifacts = CoderArtifactDraft(**artifacts_data)
        else:
            return AgentResult(success=False, reason_code="VALIDATION_FAILED")

        verdict = self.review_artifacts(
            artifacts, 
            plan_json=str(inputs.get("plan_json", "")),
            iteration=int(inputs.get("iteration", 1))
        )
        return AgentResult(success=True, payload={"verdict": verdict.model_dump(mode="json")})

