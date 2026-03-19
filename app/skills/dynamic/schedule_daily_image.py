from __future__ import annotations
from typing import Any, Dict, Optional
import os
from app.services.job_scheduler import JobScheduler


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        # Get email from input data
        to_email: str = input_data.get("email", "")

        if not to_email:
            raise ValueError("'email' is required in input_data")

        time_str: str     = input_data.get("time", "08:00")
        params: dict      = input_data.get("target_parameters", {})

        # Schedule the daily task
        from app.services.job_scheduler import JobScheduler
        scheduler = JobScheduler.get_instance()
        job_id: str = scheduler.add_job(
            skill_name="fetch_random_image",  # The name of the skill to execute (e.g. 'daily_photo_orchestrator')
            time_str=time_str,                  # The time to execute daily (e.g. '08:00')
            parameters=params,                  # Dict of inputs for the target skill
        )
        return {
            "status": "success",
            "job_id": job_id,
            "summary": f"Scheduled 'fetch_random_image' at {time_str} daily and sent to {to_email}",
        }
    except Exception as exc:
        return {"status": "error", "job_id": None, "summary": str(exc)}
