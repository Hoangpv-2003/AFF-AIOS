from __future__ import annotations
from typing import Any, Dict, Optional
import os
import json
import httpx

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        name: str      = input_data.get("name", "")
        email: str     = input_data.get("email", "")

        if not all([name, email]):
            raise ValueError("'name' and 'email' are required in input_data")

        with httpx.Client(timeout=15) as client:
            url: str  = "https://api.tavily.com/search"
            payload: dict = {
                "api_key": os.getenv("TAVILY_API_KEY", ""),
                "query": f"name:{name} email:{email}",
                "max_results": 1,
                "include_images": False,
            }

            resp = client.post(url, json=payload)
            resp.raise_for_status()

        data: dict = resp.json()
        search_result: str = data.get("results", [{}])[0].get("text", "")

        from app.services.job_scheduler import JobScheduler
        scheduler = JobScheduler.get_instance()
        job_id: str = scheduler.add_job(
            skill_name="send_email_reminder",
            time_str=search_result,
            parameters={"name": name, "email": email},
        )

        return {
            "status": "success",
            "job_id": job_id,
            "summary": f"Scheduled 'send_email_reminder' at {search_result} daily",
        }
    except Exception as exc:
        return {"status": "error", "job_id": None, "summary": str(exc)}
