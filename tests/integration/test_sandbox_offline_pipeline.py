from app.agents.reviewer import ReviewerAgent
from app.infrastructure.sandboxes.models import SandboxRequest
from app.infrastructure.sandboxes.runner import LocalSandboxRunner
from app.schemas.agents import CoderArtifactDraft, ReviewStatus


def test_reviewer_pipeline_offline_safe_artifact_passes():
    reviewer = ReviewerAgent(sandbox_runner=LocalSandboxRunner())
    artifacts = CoderArtifactDraft(
        files=["skills/dynamic/safe_skill.py"],
        rationale="local deterministic implementation",
    )

    verdict = reviewer.review_artifacts(artifacts)

    assert verdict.status == ReviewStatus.pass_
    assert verdict.reason_code is None


def test_sandbox_offline_blocks_outbound_attempt():
    runner = LocalSandboxRunner()
    result = runner.run(
        SandboxRequest(
            skill_id="net-test",
            command="python",
            args=["skills/dynamic/net_skill.py"],
            requires_network=True,
        )
    )

    assert result.success is False
    assert result.outbound_attempted is True
    assert result.outbound_blocked is True
    assert "NETWORK_EGRESS_DENIED" in result.policy_violations


def test_reviewer_pipeline_offline_network_request_fails_with_valid_verdict():
    reviewer = ReviewerAgent(sandbox_runner=LocalSandboxRunner())
    artifacts = CoderArtifactDraft(
        files=["skills/dynamic/net_skill.py"],
        rationale="requires network call to http endpoint",
    )

    verdict = reviewer.review_artifacts(artifacts)

    assert verdict.status == ReviewStatus.fail
    assert verdict.reason_code == "SANDBOX_DENIED"
    assert "NETWORK_EGRESS_DENIED" in (verdict.notes or "")
