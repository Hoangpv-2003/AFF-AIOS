"""Approval endpoints."""

from __future__ import annotations

from time import time

from fastapi import APIRouter, HTTPException

from app.schemas.approvals import ApprovalDecision, ApprovalRequestDraft, ApprovalStatus

router = APIRouter()
_APPROVALS: dict[str, dict] = {}


@router.post("/submit")
async def submit_approval(payload: ApprovalRequestDraft):
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
