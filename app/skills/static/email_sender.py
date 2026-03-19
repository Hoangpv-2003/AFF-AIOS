from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx
import email.message
from bs4 import BeautifulSoup

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    
    try:
        to_email  = input_data.get("to_email", "")
        subject   = input_data.get("subject", "Notification")
        content   = input_data.get("content", "")
        host      = os.getenv("SMTP_HOST", "")
        port      = int(os.getenv("SMTP_PORT", "587"))
        user      = os.getenv("SMTP_USER", "")
        pw        = os.getenv("SMTP_PASS") or os.getenv("SMTP_PASSWORD", "")

        if not all([to_email, host, user, pw]):
            raise ValueError("Missing: to_email, SMTP_HOST, SMTP_USER, or SMTP_PASS")

        # Get a random image from Tavily API
        with httpx.Client(timeout=15) as client:
            api_key = os.getenv("TAVILY_API_KEY", "")
            if not api_key:
                return {"status": "error", "summary": "Missing TAVILY_API_KEY environment variable"}

            query = input_data.get("query", "")
            max_results = int(input_data.get("max_results", 1))

            resp = client.post(
                "https://api.tavily.com/search",
                json={"api_key": api_key, "query": query,
                      "max_results": max_results, "include_images": True},
            )
            resp.raise_for_status()

        data = resp.json()
        image_urls = data.get("images", [])
        if not image_urls:
            return {"status": "error", "summary": "No images found"}

        # Fetch the first image
        image_url = image_urls[0]
        content += f"Image URL: {image_url}"

        # Parse HTML response with BeautifulSoup to extract image description
        resp = httpx.get(image_url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        img_description = soup.find('meta', attrs={'name': 'description'})['content']
        content += f"Image Description: {img_description}"

        # Send email with attached image and short description
        msg = email.message.Message()
        msg.set_content(content)
        msg["Subject"] = subject
        msg["From"]    = user
        msg["To"]      = to_email

        from smtplib import SMTP as Smtp
        smtp = Smtp(host, port)
        smtp.starttls()
        smtp.login(user, pw)
        smtp.send_message(msg)

        return {"status": "success", "summary": f"Email sent to {to_email}"}
    except Exception as exc:
        return {"status": "error", "summary": str(exc)}
