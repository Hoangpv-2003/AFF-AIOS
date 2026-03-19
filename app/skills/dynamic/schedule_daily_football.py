from __future__ import annotations
from typing import Any, Dict, Optional
import os
from job_scheduler import JobScheduler  # assuming this module exists


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        topic: str = input_data.get("topic", "football")
        time_str: str = input_data.get("time", "08:00")

        if not topic or not time_str:
            raise ValueError("'topic' and 'time' must be provided in input_data")

        scheduler = JobScheduler.get_instance()
        job_id: str = scheduler.add_job(
            skill_name="daily_football_workflow",
            time_str=time_str,
            parameters={"topic": topic},
        )
        return {
            "status": "success",
            "job_id": job_id,
            "summary": f"Scheduled 'daily_football_workflow' at {time_str} daily for topic '{topic}'",
        }
    except Exception as exc:
        return {"status": "error", "job_id": None, "summary": str(exc)}
