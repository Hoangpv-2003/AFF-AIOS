"""Approval endpoints."""

from __future__ import annotations

from time import time
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Response

from app.schemas.approvals import ApprovalDecision, ApprovalRequest, ApprovalStatus

router = APIRouter()
_APPROVALS: dict[str, dict] = {}

_DRAFT_SCHEMA_TOKEN = "draft"


def _apply_draft_deprecation_headers(response: Response) -> None:
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "Wed, 30 Sep 2026 00:00:00 GMT"
    response.headers["X-AAF-Migration"] = "draft->stable"


@router.post("/submit")
async def submit_approval(
    payload: ApprovalRequest,
    response: Response,
    schema_mode: Optional[str] = Header(default=None, alias="X-AAF-Schema"),
):
    if schema_mode == _DRAFT_SCHEMA_TOKEN:
        _apply_draft_deprecation_headers(response)
    approval_id = f"approval-{len(_APPROVALS) + 1}"
    _APPROVALS[approval_id] = {
        "approval_id": approval_id,
        "task_id": payload.task_id,
        "skill_id": payload.skill_id,
        "status": ApprovalStatus.pending,
        "requested_at": time(),
        "expires_at": None,
        "escalated_to": None,
    }
    return _APPROVALS[approval_id]


@router.post("/{approval_id}/decision")
async def decide_approval(approval_id: str, decision: ApprovalDecision):
    if approval_id not in _APPROVALS:
        raise HTTPException(status_code=404, detail="Approval not found")
    _APPROVALS[approval_id]["status"] = (
        ApprovalStatus.approved if decision == ApprovalDecision.approve else ApprovalStatus.rejected
    )
    return _APPROVALS[approval_id]


@router.post("/{approval_id}/escalate")
async def escalate_approval(approval_id: str):
    if approval_id not in _APPROVALS:
        raise HTTPException(status_code=404, detail="Approval not found")
    _APPROVALS[approval_id]["status"] = ApprovalStatus.escalated
    _APPROVALS[approval_id]["escalated_to"] = "fallback_reviewer"
    return _APPROVALS[approval_id]


@router.post("/{approval_id}/expire")
async def expire_approval(approval_id: str):
    if approval_id not in _APPROVALS:
        raise HTTPException(status_code=404, detail="Approval not found")
    _APPROVALS[approval_id]["status"] = ApprovalStatus.expired
    _APPROVALS[approval_id]["expires_at"] = time()
    return _APPROVALS[approval_id]


def get_approval(approval_id: str) -> dict | None:
    return _APPROVALS.get(approval_id)


def is_approval_valid(approval_id: str) -> bool:
    approval = get_approval(approval_id)
    if approval is None:
        return False
    return approval.get("status") == ApprovalStatus.approved
