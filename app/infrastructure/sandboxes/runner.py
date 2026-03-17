"""Local sandbox runner used by reviewer pipeline in offline mode."""

from __future__ import annotations

import time

from app.infrastructure.sandboxes.models import SandboxRequest, SandboxResult
from app.infrastructure.sandboxes.policy import SandboxPolicy, SandboxPolicyEvaluator


class LocalSandboxRunner:
    def __init__(self, policy: SandboxPolicy | None = None) -> None:
        self.policy = policy or SandboxPolicy(allow_network=False)
        self._evaluator = SandboxPolicyEvaluator(self.policy)

    def run(self, request: SandboxRequest) -> SandboxResult:
        started = time.perf_counter()
        violations = self._evaluator.evaluate(request)
        outbound_attempted = request.requires_network
        outbound_blocked = "NETWORK_EGRESS_DENIED" in violations

        if violations:
            return SandboxResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr=";".join(violations),
                outbound_attempted=outbound_attempted,
                outbound_blocked=outbound_blocked,
                policy_violations=violations,
                artifacts=[],
                duration_ms=int((time.perf_counter() - started) * 1000),
            )

        return SandboxResult(
            success=True,
            exit_code=0,
            stdout=f"sandbox-ok:{request.skill_id}",
            stderr="",
            outbound_attempted=outbound_attempted,
            outbound_blocked=False,
            policy_violations=[],
            artifacts=["review.log"],
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
