from app.infrastructure.sandboxes.models import SandboxRequest
from app.infrastructure.sandboxes.policy import SandboxPolicy, SandboxPolicyEvaluator


def test_sandbox_policy_blocks_outbound_network_by_default():
    evaluator = SandboxPolicyEvaluator(policy=SandboxPolicy(allow_network=False))
    request = SandboxRequest(
        skill_id="security-net-1",
        command="python",
        args=["skills/dynamic/remote.py"],
        requires_network=True,
    )

    violations = evaluator.evaluate(request)

    assert "NETWORK_EGRESS_DENIED" in violations
