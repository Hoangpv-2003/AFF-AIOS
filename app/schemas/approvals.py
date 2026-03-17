from __future__ import annotations

"""Approval schemas with draft compatibility window."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ApprovalDecision(str, Enum):
    approve = "approve"
    reject = "reject"


class ApprovalStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    expired = "expired"
    escalated = "escalated"


class ApprovalRequest(BaseModel):
    task_id: str
    skill_id: str
    requested_by: str
    reason: Optional[str] = None


class ApprovalRequestDraft(ApprovalRequest):
    """Backward-compatible request model for draft clients."""
