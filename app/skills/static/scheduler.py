from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    
    try:
        recipient: str      = input_data.get("recipient", "")
        schedule_time: str  = input_data.get("schedule_time", "08:00")
        
        if not all([recipient, schedule_time]):
            raise ValueError("'recipient' and 'schedule_time' are required in input_data")

        from app.services.job_scheduler import JobScheduler
        scheduler = JobScheduler.get_instance()
        job_id: str = scheduler.add_job(
            skill_name="image_fetcher",
            time_str=schedule_time,
            parameters={"topic": "", "data_source": ""},
        )
        
        return {
            "status": "success",
            "job_id": job_id,
            "summary": f"Scheduled image delivery for {recipient} at {schedule_time}",
        }
    except Exception as exc:
        return {"status": "error", "job_id": None, "summary": str(exc)}
