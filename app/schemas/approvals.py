from __future__ import annotations

"""Approval draft schemas."""

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


class ApprovalRequestDraft(BaseModel):
    task_id: str
    skill_id: str
    requested_by: str
    reason: Optional[str] = None
