from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx
from app.services.job_scheduler import JobScheduler


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        schedule_time: str = input_data.get("schedule_time", "08:00")

        if not schedule_time:
            raise ValueError("'schedule_time' is required in input_data")

        from app.services.job_scheduler import JobScheduler
        scheduler = JobScheduler.get_instance()
        job_id: str = scheduler.add_job(
            skill_name="orchestrator_daily_image_email",
            time_str=schedule_time,
            parameters={},
        )
        return {
            "status": "success",
            "job_id": job_id,
            "summary": f"Scheduled 'orchestrator_daily_image_email' at {schedule_time} daily",
        }
    except Exception as exc:
        return {"status": "error", "job_id": None, "summary": str(exc)}
