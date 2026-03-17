import pytest

from app.schemas.skills import SkillDigest, SkillState
from app.skills.registry import SkillRecord, SkillRegistry, SkillTransitionError


def test_skill_state_machine_allows_expected_transitions():
    reg = SkillRegistry()
    reg.register(
        SkillRecord(
            skill_id="s1",
            version="0.1.0",
            digest=SkillDigest(value="abc"),
            source_task_id="t1",
            approval_id="a1",
            status=SkillState.draft,
        )
    )

    reg.transition("s1", SkillState.reviewed)
    reg.transition("s1", SkillState.approved)

    item = reg.get("s1")
    assert item is not None
    assert item.status == SkillState.approved


def test_skill_state_machine_rejects_invalid_transition():
    reg = SkillRegistry()
    reg.register(
        SkillRecord(
            skill_id="s2",
            version="0.1.0",
            digest=SkillDigest(value="def"),
            source_task_id="t2",
            approval_id="a2",
            status=SkillState.draft,
        )
    )

    with pytest.raises(SkillTransitionError):
        reg.transition("s2", SkillState.active)
