from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
import httpx
import smtplib
from email.message import EmailMessage

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        # Extract required keys from input_data
        lottery_results: str   = input_data.get("lottery_results", "")
        recipient_email: str    = input_data.get("recipient_email", "")

        if not all([lottery_results, recipient_email]):
            raise ValueError("'lottery_results' and 'recipient_email' must be provided in input_data")

        # Set environment variables for Tavily API
        api_key: str             = os.getenv("TAVILY_API_KEY")
        tavlly_base_url: str     = "https://api.tavily.com/search"
        max_results: int         = 1

        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable is not set")

        # Search for lottery results
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                tavlly_base_url,
                json={"api_key": api_key, "query": lottery_results, "max_results": max_results, "include_images": False},
            )
            resp.raise_for_status()

        data: dict                = resp.json()
        search_results: List[dict] = data.get("results", [])

        # Extract image URLs from search results
        image_urls: List[str]     = []
        if len(search_results) > 0:
            image_url: str         = search_results[0].get("image_url", "")
            image_urls.append(image_url)

        # Set environment variables for SMTP
        smtp_host: str           = os.getenv("SMTP_HOST")
        smtp_port: int           = int(os.getenv("SMTP_PORT", "587"))
        smtp_user: str           = os.getenv("SMTP_USER")
        smtp_pw: str             = os.getenv("SMTP_PASSWORD")

        if not all([smtp_host, smtp_user, smtp_pw]):
            raise ValueError("Missing: SMTP_HOST, SMTP_USER, or SMTP_PASSWORD environment variables")

        # Prepare email content
        msg = EmailMessage()
        msg.set_content(f"Lottery results: {lottery_results}")
        msg["Subject"] = "Daily Lottery Results"
        msg["From"]    = smtp_user
        msg["To"]      = recipient_email

        # Automatically download and attach image if url is provided
        if len(image_urls) > 0:
            with httpx.Client(timeout=10) as client:
                res = client.get(image_urls[0])
                if res.status_code == 200:
                    image_data = res.content
                    maintype = "image"
                    subtype = "jpeg" # default
                    if "png" in image_urls[0].lower(): subtype = "png"
                    msg.add_attachment(image_data, maintype=maintype, subtype=subtype, filename=f"attachment.{subtype}")

        # Send Email
        with smtplib.SMTP(host=smtp_host, port=smtp_port) as smtp:
            if smtp_port == 465:
                with smtplib.SMTP_SSL(smtp_host, smtp_port) as smtp_ssl:
                    smtp_ssl.login(smtp_user, smtp_pw)
                    smtp_ssl.send_message(msg)
            else:
                smtp.starttls()
                smtp.login(smtp_user, smtp_pw)
                smtp.send_message(msg)

        return {
            "status": "success",
            "summary": f"Email sent to {recipient_email}",
            "image_urls": image_urls,
            "search_results": search_results
        }
    except httpx.HTTPStatusError as exc:
        return {"status": "error", "data": {}, "summary": f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"}
    except Exception as exc:
        return {"status": "error", "data": {}, "summary": str(exc)}
