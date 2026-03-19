from __future__ import annotations

"""Agent schemas with draft compatibility window."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ReviewStatus(str, Enum):
    pass_ = "pass"
    warn = "warn"
    fail = "fail"


class Plan(BaseModel):
    objective: str
    steps: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    architectural_decisions: Optional[dict] = Field(default=None)
    planner_notes: Optional[str] = Field(default=None)


class CoderArtifact(BaseModel):
    files: list[str] = Field(default_factory=list)
    rationale: str


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
