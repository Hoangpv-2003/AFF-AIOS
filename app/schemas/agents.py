from __future__ import annotations

"""Agent draft contracts."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ReviewStatus(str, Enum):
    pass_ = "pass"
    warn = "warn"
    fail = "fail"


class PlanDraft(BaseModel):
    objective: str
    steps: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class CoderArtifactDraft(BaseModel):
    files: list[str] = Field(default_factory=list)
    rationale: str


class ReviewVerdictDraft(BaseModel):
    status: ReviewStatus
    reason_code: Optional[str] = None
    notes: Optional[str] = None
