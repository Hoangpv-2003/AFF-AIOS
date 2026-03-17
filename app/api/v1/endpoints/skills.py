"""Skill endpoints."""

from fastapi import APIRouter, HTTPException

from app.api.v1.endpoints.approvals import is_approval_valid
from app.schemas.skills import SkillManifestDraft, SkillRegisterRequest, SkillState
from app.skills.registry import SkillRecord, SkillTransitionError, registry

router = APIRouter()


def _to_manifest(record: SkillRecord) -> SkillManifestDraft:
    return SkillManifestDraft(
        skill_id=record.skill_id,
        version=record.version,
        state=record.status,
        digest=record.digest,
        source_task_id=record.source_task_id,
        approval_id=record.approval_id,
        activated_at=record.activated_at,
    )


@router.post("/register", response_model=SkillManifestDraft)
async def register_skill(payload: SkillRegisterRequest):
    record = SkillRecord(
        skill_id=payload.skill_id,
        version=payload.version,
        digest=payload.digest,
        source_task_id=payload.source_task_id,
        approval_id=payload.approval_id,
        status=payload.status,
    )
    return _to_manifest(registry.register(record))


@router.get("", response_model=list[SkillManifestDraft])
async def list_skills():
    return [_to_manifest(item) for item in registry.list()]


@router.get("/{skill_id}", response_model=SkillManifestDraft)
async def get_skill(skill_id: str):
    item = registry.get(skill_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return _to_manifest(item)


@router.post("/{skill_id}/activate", response_model=SkillManifestDraft)
async def activate_skill(skill_id: str):
    item = registry.get(skill_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    try:
        activated = registry.activate(skill_id, is_approval_valid(item.approval_id))
    except SkillTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_manifest(activated)


@router.post("/{skill_id}/quarantine", response_model=SkillManifestDraft)
async def quarantine_skill(skill_id: str):
    if registry.get(skill_id) is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    try:
        quarantined = registry.transition(skill_id, SkillState.quarantined)
    except SkillTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_manifest(quarantined)
