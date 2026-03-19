from __future__ import annotations
from typing import Any, Dict, Optional
import os
from app.services.job_scheduler import JobScheduler  # type: ignore


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        target_skill_name: str = "daily_scheduled_image"
        time_str: str = input_data.get("time", "08:00")
        parameters: dict = {}

        if not time_str:
            raise ValueError("'time' is required in input_data")

        from app.services.job_scheduler import JobScheduler
        scheduler = JobScheduler.get_instance()
        job_id: str = scheduler.add_job(
            skill_name=target_skill_name,  # The name of the skill to execute (e.g. 'daily_photo_orchestrator')
            time_str=time_str,      # The time to execute daily (e.g. '08:00')
            parameters=parameters,      # Dict of inputs for the target skill
        )
        return {
            "status": "success",
            "job_id": job_id,
            "summary": f"Scheduled '{target_skill_name}' at {time_str} daily",
        }
    except Exception as exc:
        return {"status": "error", "job_id": None, "summary": str(exc)}
