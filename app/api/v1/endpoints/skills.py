"""Skill endpoints."""

from fastapi import APIRouter, HTTPException

from app.schemas.skills import SkillManifestDraft, SkillState

router = APIRouter()
_SKILLS: dict[str, SkillManifestDraft] = {}


@router.get("", response_model=list[SkillManifestDraft])
async def list_skills():
    return list(_SKILLS.values())


@router.get("/{skill_id}", response_model=SkillManifestDraft)
async def get_skill(skill_id: str):
    if skill_id not in _SKILLS:
        raise HTTPException(status_code=404, detail="Skill not found")
    return _SKILLS[skill_id]


@router.post("/{skill_id}/activate", response_model=SkillManifestDraft)
async def activate_skill(skill_id: str):
    if skill_id not in _SKILLS:
        raise HTTPException(status_code=404, detail="Skill not found")
    skill = _SKILLS[skill_id]
    if skill.state not in {SkillState.approved, SkillState.reviewed}:
        raise HTTPException(status_code=400, detail="Skill is not approved")
    skill.state = SkillState.active
    _SKILLS[skill_id] = skill
    return skill


@router.post("/{skill_id}/quarantine", response_model=SkillManifestDraft)
async def quarantine_skill(skill_id: str):
    if skill_id not in _SKILLS:
        raise HTTPException(status_code=404, detail="Skill not found")
    skill = _SKILLS[skill_id]
    skill.state = SkillState.quarantined
    _SKILLS[skill_id] = skill
    return skill
