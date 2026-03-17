from app.agents.base_agent import AgentContext, AgentResult
from app.agents.manager import ManagerAgent
from app.agents.reviewer import ReviewerAgent


class WarnThenPassReviewer(ReviewerAgent):
    def __init__(self):
        self.calls = 0

    def act(self, context: AgentContext, inputs):
        self.calls += 1
        if self.calls == 1:
            return AgentResult(
                success=True,
                payload={
                    "verdict": {
                        "status": "warn",
                        "reason_code": "VALIDATION_FAILED",
                    }
                },
            )
        return AgentResult(success=True, payload={"verdict": {"status": "pass"}})


class AlwaysWarnReviewer(ReviewerAgent):
    def act(self, context: AgentContext, inputs):
        return AgentResult(
            success=True,
            payload={
                "verdict": {
                    "status": "warn",
                    "reason_code": "VALIDATION_FAILED",
                }
            },
        )


def test_manager_retries_on_warn_then_passes():
    manager = ManagerAgent(reviewer=WarnThenPassReviewer(), retry_on_warn=True, max_warn_retries=1)
    result = manager.run(task_id="t2", prompt="Do planning")

    assert result.final_state == "WAITING_APPROVAL"
    assert result.transitions.count("CODED") == 2
    assert "REVIEWED_WARN" in result.transitions
    assert "REVIEWED_PASS" in result.transitions


def test_manager_escalates_to_waiting_approval_when_warn_persists():
    manager = ManagerAgent(reviewer=AlwaysWarnReviewer(), retry_on_warn=False)
    result = manager.run(task_id="t3", prompt="Do planning")

    assert result.final_state == "WAITING_APPROVAL"
    assert result.reason_code == "VALIDATION_FAILED"
    assert "REVIEWED_WARN" in result.transitions
