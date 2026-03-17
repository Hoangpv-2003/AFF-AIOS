from app.agents.manager import ManagerAgent


def test_manager_fails_with_timeout_reason_when_forced():
    manager = ManagerAgent()
    result = manager.run(
        task_id="t-timeout",
        prompt="Implement queue handling",
        fail_at_state="PLANNED",
    )

    assert result.final_state == "FAILED"
    assert result.reason_code == "TIMEOUT"
