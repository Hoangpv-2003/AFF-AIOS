from __future__ import annotations
from typing import Any, Dict, Optional
import os


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        # Hardcode the master orchestrator skill name here if not provided in input
        target_skill: str = input_data.get("target_skill", "orchestrator_daily_lottery_results")
        time_str: str     = input_data.get("time", "2024-01-04T19:00")  # Two weeks from now

        if target_skill == "":
            raise ValueError("'target_skill' must be provided or hardcoded")

        from app.services.job_scheduler import JobScheduler
        scheduler = JobScheduler.get_instance()
        job_id: str = scheduler.add_job(
            skill_name=target_skill,  # The name of the skill to execute (e.g. 'daily_photo_orchestrator')
            time_str=time_str,      # The time to execute daily (e.g. '08:00')
            parameters={},          # Dict of inputs for the target skill
        )
        return {
            "status": "success",
            "job_id": job_id,
            "summary": f"Scheduled '{target_skill}' at {time_str} daily",
        }
    except Exception as exc:
        return {"status": "error", "job_id": None, "summary": str(exc)}
