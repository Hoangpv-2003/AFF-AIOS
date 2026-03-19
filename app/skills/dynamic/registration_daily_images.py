from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        # Retrieve necessary environment variables safely
        api_key: str = os.environ.get("TAVILY_API_KEY")
        smtp_host: str = os.environ.get("SMTP_HOST")
        smtp_port: int = int(os.environ.get("SMTP_PORT", "465"))
        smtp_user: str = os.environ.get("SMTP_USER")
        smtp_password: str = os.environ.get("SMTP_PASSWORD")

        if not api_key or not smtp_host or not smtp_user or not smtp_password:
            raise ValueError("Missing environment variables for Tavily API key, SMTP host, user, and password")

        # Define target skill name (should be hardcoded)
        target_skill_name: str = "orchestrator_daily_images"

        from app.services.job_scheduler import JobScheduler
        scheduler = JobScheduler.get_instance()
        job_id: str = scheduler.add_job(
            skill_name=target_skill_name,
            time_str="08:00",
            parameters={},
        )
        return {
            "status": "success",
            "job_id": job_id,
            "summary": f"Scheduled '{target_skill_name}' at 08:00 daily",
        }
    except Exception as exc:
        return {"status": "error", "job_id": None, "summary": str(exc)}
