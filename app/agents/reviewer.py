"""Reviewer agent implementation for static checks and verdict emission."""

from __future__ import annotations

from typing import Dict

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

    def review_artifacts(self, artifacts: CoderArtifactDraft, plan_json: str = "", iteration: int = 1) -> Dict[str, Any]:
        if not artifacts.generated_code:
            return {"is_approved": False, "review_feedback": "No code generated."}

        # 1. Static Security Heuristics
        code = artifacts.generated_code.lower()
        if "os.system" in code or "subprocess.popen" in code:
             return {"is_approved": False, "review_feedback": "Phát hiện lệnh thực thi hệ thống không an toàn (os.system/subprocess)."}

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
                return {
                    "is_approved": bool(parsed.get("is_approved", False)),
                    "review_feedback": str(parsed.get("review_feedback", ""))
                }
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
            return {
                "is_approved": False, 
                "review_feedback": f"Sandbox error: {result.stderr}"
            }
            
        return {"is_approved": True, "review_feedback": "Code looks good."}

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
        return AgentResult(success=True, payload={"verdict": verdict})

