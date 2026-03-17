"""Approval endpoints."""

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
    return _APPROVALS[approval_id]


@router.post("/{approval_id}/expire")
async def expire_approval(approval_id: str):
    if approval_id not in _APPROVALS:
        raise HTTPException(status_code=404, detail="Approval not found")
    _APPROVALS[approval_id]["status"] = ApprovalStatus.expired
    return _APPROVALS[approval_id]
