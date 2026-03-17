"""Skill drift reconciliation service."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from time import time
from typing import Dict, List

from app.schemas.skills import SkillState
from app.skills.registry import SkillRegistry, SkillTransitionError


@dataclass
class DriftRecord:
    skill_id: str
    reason: str
    registry_digest: str
    runtime_digest: str | None
    git_digest: str | None


@dataclass
class ReconciliationResult:
    run_id: str
    status: str
    drift_count: int
    quarantined_skills: List[str]
    drifts: List[DriftRecord]
    started_at: float

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "drift_count": self.drift_count,
            "quarantined_skills": self.quarantined_skills,
            "drifts": [asdict(item) for item in self.drifts],
            "started_at": self.started_at,
        }


class ReconciliationService:
    def __init__(self) -> None:
        self._runtime_snapshot: Dict[str, str] = {}
        self._git_snapshot: Dict[str, str] = {}
        self._last_result: ReconciliationResult | None = None

    def set_runtime_digest(self, skill_id: str, digest: str) -> None:
        self._runtime_snapshot[skill_id] = digest

    def set_git_digest(self, skill_id: str, digest: str) -> None:
        self._git_snapshot[skill_id] = digest

    def reset(self) -> None:
        self._runtime_snapshot = {}
        self._git_snapshot = {}
        self._last_result = None

    def run(self, registry: SkillRegistry) -> ReconciliationResult:
        started_at = time()
        run_id = f"reconcile-{int(started_at * 1000)}"
        drifts: List[DriftRecord] = []
        quarantined_skills: List[str] = []

        for record in registry.list():
            if record.status == SkillState.deprecated:
                continue

            runtime_digest = self._runtime_snapshot.get(record.skill_id)
            git_digest = self._git_snapshot.get(record.skill_id)
            registry_digest = record.digest.value

            reason = ""
            if runtime_digest is None:
                reason = "missing_runtime_digest"
            elif runtime_digest != registry_digest:
                reason = "runtime_digest_mismatch"
            elif git_digest is None:
                reason = "missing_git_digest"
            elif git_digest != registry_digest:
                reason = "git_digest_mismatch"

            if not reason:
                continue

            drifts.append(
                DriftRecord(
                    skill_id=record.skill_id,
                    reason=reason,
                    registry_digest=registry_digest,
                    runtime_digest=runtime_digest,
                    git_digest=git_digest,
                )
            )

            if record.status not in {SkillState.quarantined, SkillState.deprecated}:
                try:
                    registry.transition(record.skill_id, SkillState.quarantined)
                    quarantined_skills.append(record.skill_id)
                except SkillTransitionError:
                    # Ignore non-quarantinable states in this pass.
                    pass

        result = ReconciliationResult(
            run_id=run_id,
            status="completed",
            drift_count=len(drifts),
            quarantined_skills=quarantined_skills,
            drifts=drifts,
            started_at=started_at,
        )
        self._last_result = result
        return result

    def get_status(self) -> dict:
        if self._last_result is None:
            return {"status": "idle"}
        return self._last_result.to_dict()


reconciliation_service = ReconciliationService()
