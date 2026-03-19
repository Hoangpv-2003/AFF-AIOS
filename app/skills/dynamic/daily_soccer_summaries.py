from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx
from bs4 import BeautifulSoup
from email.message import EmailMessage
import smtplib
from job_scheduler import JobScheduler

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    
    try:
        # Retrieve soccer results from Tavily API
        query: str = input_data.get("query", "")
        max_results: int = int(input_data.get("max_results", 5))
        api_key: str = os.getenv("TAVILY_API_KEY", "")

        if not query:
            raise ValueError("'query' is required in input_data")
        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable is not set")

        with httpx.Client(timeout=15) as client:
            resp = client.post(
                "https://api.tavily.com/search",
                json={"api_key": api_key, "query": query,
                      "max_results": max_results, "include_images": True},
            )
            resp.raise_for_status()

        data: dict = resp.json()
        image_urls: List[str] = data.get("images", [])
        results: List[dict] = data.get("results", [])

        # Generate summary
        summary: str = ""
        for result in results:
            title: str = result.get("title") or ""
            description: str = result.get("description") or ""
            image_url: str = result.get("image_url") or ""

            if image_url == "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800":
                summary += f"Image: {image_url}\n"
            elif image_url == "https://images.unsplash.com/photo-1449034446853-66c86144b0ad?w=800":
                summary += f"Image: {image_url}\n"

            summary += f"{title}: {description}\n\n"

        # Send email with summary
        to_email: str = input_data.get("to_email") or input_data.get("email", "")
        subject: str = "Daily Soccer Summaries"
        content: str = summary

        if not all([to_email]):
            raise ValueError("Missing: to_email")

        msg = EmailMessage()
        msg.set_content(content)
        msg["Subject"] = subject
        msg["From"]    = os.getenv("SMTP_FROM", "")
        msg["To"]      = to_email

        with smtplib.SMTP(os.getenv("SMTP_HOST", ""), int(os.getenv("SMTP_PORT", "587"))) as smtp:
            smtp.starttls()
            smtp.login(os.getenv("SMTP_USER", ""), os.getenv("SMTP_PASSWORD", ""))
            smtp.send_message(msg)

        return {
            "status": "success",
            "summary": summary,
        }
    except Exception as exc:
        return {"status": "error", "summary": str(exc)}
