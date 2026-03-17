"""Manual skills reconciliation endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/run")
async def run_reconciliation():
    return {"status": "started"}


@router.get("/status")
async def get_reconciliation_status():
    return {"status": "idle"}
