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


@router.post("/{skill_id}/recover", response_model=SkillManifestDraft)
async def recover_skill(skill_id: str):
    if registry.get(skill_id) is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    try:
        recovered = registry.recover(skill_id)
    except SkillTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_manifest(recovered)


@router.post("/{skill_id}/execute")
async def execute_skill(skill_id: str):
    item = registry.get(skill_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    if item.status == SkillState.quarantined:
        raise HTTPException(status_code=423, detail="Skill is quarantined due to detected drift")
    if item.status != SkillState.active:
        raise HTTPException(status_code=400, detail="Skill must be active before execute")
    return {"skill_id": skill_id, "status": "executed"}
