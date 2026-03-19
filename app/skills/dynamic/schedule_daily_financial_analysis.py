from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx
from app.services.job_scheduler import JobScheduler  # Assuming this module exists

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        target_skill: str = "daily_financial_analysis_workflow"
        time_str: str     = "2024-01-01 08:00" # hardcoded time for demonstration
        params: dict      = {} # empty dictionary

        if not all([target_skill, time_str]):
            raise ValueError("'target_skill' and 'time' must be provided")

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
