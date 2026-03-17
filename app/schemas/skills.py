from __future__ import annotations

"""Skill schemas with draft compatibility window."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class SkillState(str, Enum):
    draft = "draft"
    reviewed = "reviewed"
    approved = "approved"
    active = "active"
    quarantined = "quarantined"
    deprecated = "deprecated"


class SkillDigest(BaseModel):
    algorithm: str = "sha256"
    value: str


class SkillManifest(BaseModel):
    skill_id: str
    version: str
    state: SkillState = SkillState.draft
    digest: Optional[SkillDigest] = None
    source_task_id: Optional[str] = None
    approval_id: Optional[str] = None
    activated_at: Optional[float] = None


class SkillManifestDraft(SkillManifest):
    """Backward-compatible response model for draft clients."""


class SkillRegisterRequest(BaseModel):
    skill_id: str
    version: str
    digest: SkillDigest
    source_task_id: str
    approval_id: str
    status: SkillState = SkillState.draft
