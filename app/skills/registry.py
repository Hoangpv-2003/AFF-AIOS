import os
import json
import pymongo
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
    is_static: bool = False


class SkillRegistry:
    VALID_TRANSITIONS = {
        SkillState.draft: {SkillState.reviewed, SkillState.quarantined, SkillState.deprecated},
        SkillState.reviewed: {SkillState.approved, SkillState.quarantined, SkillState.deprecated},
        SkillState.approved: {SkillState.active, SkillState.quarantined, SkillState.deprecated},
        SkillState.active: {SkillState.quarantined, SkillState.deprecated},
        SkillState.quarantined: {SkillState.reviewed, SkillState.approved, SkillState.deprecated},
        SkillState.deprecated: set(),
    }

    def __init__(self) -> None:
        self._skills: Dict[str, SkillRecord] = {}
        self._db = None

    def _get_collection(self):
        try:
            if self._db is None:
                mongo_uri = os.getenv("MONGODB_URI")
                mongo_db = os.getenv("MONGODB_DB", "agentic")
                if not mongo_uri:
                    return None
                client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
                self._db = client[mongo_db]
            return self._db["skill_registry"]
        except Exception:
            return None

    def load_from_db(self) -> None:
        col = self._get_collection()
        if col is None:
            return
        try:
            for doc in col.find():
                skill_id = doc["skill_id"]
                record = SkillRecord(
                    skill_id=doc["skill_id"],
                    version=doc["version"],
                    digest=SkillDigest(**doc["digest"]),
                    source_task_id=doc["source_task_id"],
                    approval_id=doc["approval_id"],
                    status=SkillState(doc["status"]),
                    activated_at=doc.get("activated_at"),
                    is_static=doc.get("is_static", False)
                )
                self._skills[skill_id] = record
        except Exception:
            pass

    def _persist(self, record: SkillRecord) -> None:
        col = self._get_collection()
        if col is None:
            return
        try:
            doc = {
                "skill_id": record.skill_id,
                "version": record.version,
                "digest": record.digest.model_dump() if hasattr(record.digest, "model_dump") else record.digest,
                "source_task_id": record.source_task_id,
                "approval_id": record.approval_id,
                "status": record.status.value,
                "activated_at": record.activated_at,
                "is_static": record.is_static
            }
            col.update_one({"skill_id": record.skill_id}, {"$set": doc}, upsert=True)
        except Exception:
            pass

    def register(self, record: SkillRecord) -> SkillRecord:
        self._skills[record.skill_id] = record
        self._persist(record)
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
        self._persist(record)
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

    def recover(self, skill_id: str, target_state: SkillState = SkillState.reviewed) -> SkillRecord:
        record = self._skills.get(skill_id)
        if record is None:
            raise SkillTransitionError("Skill not found")
        if record.status != SkillState.quarantined:
            raise SkillTransitionError("Only quarantined skills can be recovered")
        if target_state not in {SkillState.reviewed, SkillState.approved}:
            raise SkillTransitionError("Recovery target must be reviewed or approved")
        return self.transition(skill_id, target_state)


registry = SkillRegistry()

