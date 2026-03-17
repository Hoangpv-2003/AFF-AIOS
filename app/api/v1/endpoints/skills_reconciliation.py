"""Manual skills reconciliation endpoints."""

from fastapi import APIRouter

from app.infrastructure.reconciliation.reconcile_service import reconciliation_service
from app.skills.registry import registry

router = APIRouter()


@router.post("/run")
async def run_reconciliation():
    return reconciliation_service.run(registry).to_dict()


@router.post("/seed/runtime/{skill_id}")
async def seed_runtime_digest(skill_id: str, digest: str):
    reconciliation_service.set_runtime_digest(skill_id, digest)
    return {"status": "ok", "scope": "runtime", "skill_id": skill_id}


@router.post("/seed/git/{skill_id}")
async def seed_git_digest(skill_id: str, digest: str):
    reconciliation_service.set_git_digest(skill_id, digest)
    return {"status": "ok", "scope": "git", "skill_id": skill_id}


@router.get("/status")
async def get_reconciliation_status():
    return reconciliation_service.get_status()
