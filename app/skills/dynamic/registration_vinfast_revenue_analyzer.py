from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        # Hardcode the master orchestrator skill name here if not provided in input
        target_skill: str = input_data.get("target_skill", "vinfast_revenue_analyzer")
        time_str: str     = input_data.get("time", "08:00")
        params: dict      = input_data.get("target_parameters", {})

        from app.services.job_scheduler import JobScheduler
        scheduler = JobScheduler.get_instance()
        
        # Remove hardcoded skill name and replace it with a variable from the input data
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
