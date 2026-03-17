import pytest

from app.agents.manager import ManagerAgent


def test_manager_blocks_illegal_state_transition():
    manager = ManagerAgent()
    with pytest.raises(ValueError):
        manager.transition("RECEIVED", "ACTIVATED")
