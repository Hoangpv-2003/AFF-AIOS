from app.agents.base_agent import AgentContext, AgentResult
from app.agents.manager import ManagerAgent
from app.agents.reviewer import ReviewerAgent


class UnavailableReviewer(ReviewerAgent):
    def act(self, context: AgentContext, inputs):
        return AgentResult(success=False, reason_code="PROVIDER_ERROR")


def test_reviewer_unavailable_escalates_to_waiting_approval():
    manager = ManagerAgent(reviewer=UnavailableReviewer())
    result = manager.run(task_id="chaos-r1", prompt="create endpoint")

    assert result.final_state == "WAITING_APPROVAL"
    assert result.reason_code == "PROVIDER_ERROR"
    assert "REVIEWED_WARN" in result.transitions
    assert result.transitions[-1] == "WAITING_APPROVAL"
