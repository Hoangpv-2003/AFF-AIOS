from __future__ import annotations

"""Agent schemas with draft compatibility window."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ReviewStatus(str, Enum):
    pass_ = "pass"
    warn = "warn"
    fail = "fail"


class SkillKind(str, Enum):
    retrieve = "retrieve"
    generate = "generate"
    deliver = "deliver"
    schedule = "schedule"
    analyse = "analyse"
    mutate = "mutate"


class SkillSpec(BaseModel):
    skill_name: str
    skill_kind: SkillKind = SkillKind.generate
    is_static: bool = False
    skill_purpose: str
    input_keys: list[str] = Field(default_factory=list)
    output_keys: list[str] = Field(default_factory=list)
    coder_notes: str


class Plan(BaseModel):
    task_summary: str
    skills_to_create: list[SkillSpec] = Field(default_factory=list)
    confidence: float = 0.0


class CoderArtifact(BaseModel):
    files: list[str] = Field(default_factory=list)
    rationale: str
    generated_code: str = ""
    schema_json: str = ""


class ReviewVerdict(BaseModel):
    status: ReviewStatus
    reason_code: Optional[str] = None
    notes: Optional[str] = None


class PlanDraft(Plan):
    """Backward-compatible plan model for draft clients."""


class CoderArtifactDraft(CoderArtifact):
    """Backward-compatible coder artifact model for draft clients."""


class ReviewVerdictDraft(ReviewVerdict):
    """Backward-compatible review verdict model for draft clients."""
