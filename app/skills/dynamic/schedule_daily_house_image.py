from __future__ import annotations
from typing import Any, Dict, Optional
import os


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        target_skill: str = input_data.get("target_skill", "daily_house_image_workflow")
        time_str: str     = input_data.get("time", "08:00")

        if not all([target_skill, time_str]):
            raise ValueError("'target_skill' and 'time' must be provided in input_data")

        from app.services.job_scheduler import JobScheduler
        scheduler = JobScheduler.get_instance()
        job_id: str = scheduler.add_job(
            skill_name=target_skill,
            time_str=time_str,
            parameters={},
        )
        return {
            "status": "success",
            "job_id": job_id,
            "summary": f"Scheduled '{target_skill}' at {time_str} daily",
        }
    except Exception as exc:
        return {"status": "error", "job_id": None, "summary": str(exc)}
