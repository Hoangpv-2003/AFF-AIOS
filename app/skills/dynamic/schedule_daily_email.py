from __future__ import annotations
from typing import Any, Dict, Optional
import httpx


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        # Hardcode the master orchestrator skill name here if not provided in input
        target_skill: str = input_data.get("target_skill", "daily_email_orchestrator")
        time_str: str     = input_data.get("time", "08:00")

        from app.services.job_scheduler import JobScheduler
        scheduler = httpx.get('http://localhost:5000/job_scheduler').json()['instance']
        job_id: str = scheduler.add_job(
            skill_name=target_skill, # The name of the skill to execute (e.g. 'daily_photo_orchestrator')
            time_str=time_str,      # The time to execute daily (e.g. '08:00')
        )
        return {
            "status": "success",
            "job_id": job_id,
            "summary": f"Scheduled '{target_skill}' at {time_str} daily",
        }
    except Exception as exc:
        return {"status": "error", "job_id": None, "summary": str(exc)}
