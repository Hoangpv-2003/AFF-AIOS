from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx
from app.services.job_scheduler import JobScheduler

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        # Hardcode the master orchestrator skill name here if not provided in input
        target_skill: str = input_data.get("target_skill", "search_images")
        time_str: str     = input_data.get("time", "08:00")
        params: dict      = {}

        # Get search results from 'search_images' skill
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                "https://api.tavily.com/search",
                json={"api_key": os.getenv("TAVILY_API_KEY", ""),
                      "query": "dog or cat images",
                      "max_results": 5, "include_images": True},
            )
            resp.raise_for_status()

        data: dict            = resp.json()
        image_urls: List[str] = data.get("images", [])

        # Get email parameters from environment variables
        to_email: str         = os.getenv("TO_EMAIL", "")
        subject: str          = "Daily Images of Dogs and Cats"
        content: str          = ""
        host: str             = os.getenv("SMTP_HOST", "")
        port: int             = int(os.getenv("SMTP_PORT", "465"))
        user: str             = os.getenv("SMTP_USER", "")
        pw: str               = os.getenv("SMTP_PASS") or os.getenv("SMTP_PASSWORD", "")

        if not all([to_email, host, user, pw]):
            raise ValueError("Missing: TO_EMAIL, SMTP_HOST, SMTP_USER, or SMTP_PASS")

        # Send email with images
        msg = httpx.post(
            "https://api.email.com/send",
            json={
                "to": to_email,
                "subject": subject,
                "content": content,
                "image_urls": image_urls
            }
        )
        if msg.status_code == 200:
            return {
                "status": "success",
                "summary": f"Daily images of dogs and cats sent to {to_email} successfully"
            }

        # Register the orchestrator skill to run daily at 08:00
        scheduler = JobScheduler.get_instance()
        job_id: str = scheduler.add_job(
            skill_name="orchestrator_daily_images",
            time_str=time_str,
            parameters=params,
        )
        return {
            "status": "success",
            "job_id": job_id,
            "summary": f"Scheduled 'orchestrator_daily_images' at {time_str} daily"
        }
    except Exception as exc:
        return {"status": "error", "job_id": None, "summary": str(exc)}
