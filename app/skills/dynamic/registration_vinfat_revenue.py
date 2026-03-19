from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx
from app.services.job_scheduler import JobScheduler


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        target_skill: str = input_data.get("target_skill", "vinfast_revenue_analyzer")
        time_str: str     = input_data.get("time", "08:00")
        params: dict      = input_data.get("target_parameters", {})

        if not target_skill or target_skill == "replace_with_hardcoded_name":
            raise ValueError("'target_skill' must be provided or hardcoded")

        scheduler = JobScheduler.get_instance()
        job_id: str = scheduler.add_job(
            skill_name=target_skill, 
            time_str=time_str,     
            parameters=params,     
        )
        return {
            "status": "success",
            "job_id": job_id,
            "summary": f"Scheduled '{target_skill}' at {time_str} daily",
        }
    except Exception as exc:
        return {"status": "error", "job_id": None, "summary": str(exc)}
