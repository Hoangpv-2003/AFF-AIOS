from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
import httpx
from bs4 import BeautifulSoup
import smtplib
from email.message import EmailMessage


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    
    try:
        # Get necessary information from environment variables and input data
        TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY")
        SMTP_HOST: str     = os.getenv("SMTP_HOST")
        SMTP_PORT: int     = int(os.getenv("SMTP_PORT", "587"))
        SMTP_USER: str     = os.getenv("SMTP_USER")
        SMTP_PASSWORD: str = os.getenv("SMTP_PASS")

        query: str = input_data.get("query", "")

        # If necessary information is missing, raise an error
        if not TAVILY_API_KEY or not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD:
            raise ValueError("Missing environment variable(s): TAVILY_API_KEY, SMTP_HOST, SMTP_USER, SMTP_PASS")
        
        # Send a POST request to the Tavily API with the query string
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                "https://api.tavily.com/search",
                json={"api_key": TAVILY_API_KEY, "query": query,
                      "max_results": 1, "include_images": True},
            )
            resp.raise_for_status()

        # Parse the JSON response
        data: dict = resp.json()
        
        # Get the image URL and description from the response
        image_url: str = data.get("images", [])[0]
        description: str = BeautifulSoup(data.get("description", ""), "html.parser").get_text()
        
        # Send an email with the image and description
        msg = EmailMessage()
        msg.set_content(description)
        msg["Subject"] = "Daily Image"
        msg["From"]    = SMTP_USER
        msg["To"]      = input_data.get("email", "")

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)

        # Return the result
        return {
            "status": "success",
            "summary": f"Sent daily image to {input_data.get('email', '')}",
            "image_url": image_url,
            "description": description,
        }
    except Exception as exc:
        return {"status": "error", "summary": str(exc), "image_url": "", "description": ""}
