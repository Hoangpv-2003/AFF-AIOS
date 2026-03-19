from __future__ import annotations
from typing import Any, Dict, Optional
import os
from app.services.job_scheduler import JobScheduler


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        target_skill: str = "daily_soccer_summaries"
        time_str: str     = "08:00"

        scheduler = JobScheduler.get_instance()
        job_id: str = scheduler.add_job(
            skill_name=target_skill,
            time_str=time_str,
        )
        return {
            "status": "success",
            "job_id": job_id,
            "summary": f"Scheduled '{target_skill}' at {time_str} daily",
        }
    except Exception as exc:
        return {"status": "error", "job_id": None, "summary": str(exc)}
