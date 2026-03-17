"""Agent debugging endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/run")
async def run_debug_agent_flow():
    return {"message": "agent debug flow queued"}


@router.get("/steps")
async def list_agent_steps():
    return {"steps": []}
