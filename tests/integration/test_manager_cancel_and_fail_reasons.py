from app.agents.manager import ManagerAgent


def test_manager_cancels_with_user_cancelled_reason():
    manager = ManagerAgent()
    result = manager.run(task_id="t4", prompt="Create api", cancel_at_state="CODED")

    assert result.final_state == "CANCELLED"
    assert result.reason_code == "USER_CANCELLED"


def test_manager_fail_reason_is_set_for_timeout():
    manager = ManagerAgent()
    result = manager.run(task_id="t5", prompt="Create api", fail_at_state="PLANNED")

    assert result.final_state == "FAILED"
    assert result.reason_code == "TIMEOUT"
