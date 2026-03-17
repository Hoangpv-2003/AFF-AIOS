"""API router composition for versioned endpoints."""

from fastapi import APIRouter

from app.api.v1.endpoints import agents, approvals, skills, skills_reconciliation, tasks, traces
from app.core.constants import API_V1_PREFIX


api_router = APIRouter(prefix=API_V1_PREFIX)
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(skills.router, prefix="/skills", tags=["skills"])
api_router.include_router(skills_reconciliation.router, prefix="/skills/reconciliation", tags=["reconciliation"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
api_router.include_router(traces.router, prefix="/traces", tags=["traces"])

