"""In-memory skill registry with lifecycle transitions and activation guards."""

from __future__ import annotations

from dataclasses import dataclass
from time import time
from typing import Dict, List, Optional

from app.schemas.skills import SkillDigest, SkillState


class SkillTransitionError(ValueError):
	"""Raised when an invalid state transition is requested."""


@dataclass
class SkillRecord:
	skill_id: str
	version: str
	digest: SkillDigest
	source_task_id: str
	approval_id: str
	status: SkillState = SkillState.draft
	activated_at: Optional[float] = None


class SkillRegistry:
	VALID_TRANSITIONS = {
		SkillState.draft: {SkillState.reviewed, SkillState.quarantined, SkillState.deprecated},
		SkillState.reviewed: {SkillState.approved, SkillState.quarantined, SkillState.deprecated},
		SkillState.approved: {SkillState.active, SkillState.quarantined, SkillState.deprecated},
		SkillState.active: {SkillState.quarantined, SkillState.deprecated},
		SkillState.quarantined: {SkillState.reviewed, SkillState.deprecated},
		SkillState.deprecated: set(),
	}

	def __init__(self) -> None:
		self._skills: Dict[str, SkillRecord] = {}

	def register(self, record: SkillRecord) -> SkillRecord:
		self._skills[record.skill_id] = record
		return record

	def get(self, skill_id: str) -> Optional[SkillRecord]:
		return self._skills.get(skill_id)

	def list(self) -> List[SkillRecord]:
		return list(self._skills.values())

	def transition(self, skill_id: str, next_state: SkillState) -> SkillRecord:
		record = self._skills.get(skill_id)
		if record is None:
			raise SkillTransitionError("Skill not found")

		allowed = self.VALID_TRANSITIONS.get(record.status, set())
		if next_state not in allowed:
			raise SkillTransitionError(
				f"Invalid transition: {record.status.value} -> {next_state.value}"
			)

		record.status = next_state
		if next_state == SkillState.active:
			record.activated_at = time()
		self._skills[skill_id] = record
		return record

	def activate(self, skill_id: str, approval_valid: bool) -> SkillRecord:
		record = self._skills.get(skill_id)
		if record is None:
			raise SkillTransitionError("Skill not found")
		if not approval_valid:
			raise SkillTransitionError("Approval is not valid")
		if record.status != SkillState.approved:
			raise SkillTransitionError("Skill must be approved before activation")
		return self.transition(skill_id, SkillState.active)


registry = SkillRegistry()

