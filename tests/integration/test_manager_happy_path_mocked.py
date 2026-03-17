from app.agents.manager import ManagerAgent


def test_manager_happy_path_reaches_waiting_approval():
    manager = ManagerAgent()
    result = manager.run(task_id="t1", prompt="Build auth endpoint. Add tests.")

    assert result.final_state == "WAITING_APPROVAL"
    assert "RECEIVED" in result.transitions
    assert "PLANNED" in result.transitions
    assert "CODED" in result.transitions
    assert "REVIEWED_PASS" in result.transitions
