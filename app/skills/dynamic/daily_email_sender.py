from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx
from bs4 import BeautifulSoup

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        image_url: str = input_data.get("image_url", "")
        image_description: str = input_data.get("image_description", "")

        if not all([image_url, image_description]):
            raise ValueError("'image_url' and 'image_description' are required in input_data")

        subject: str  = "Daily Image"
        to_email: str = os.getenv("EMAIL_TO", "tuanm7530@gmail.com")
        host: str     = os.getenv("SMTP_HOST", "")
        port: int     = int(os.getenv("SMTP_PORT", "587"))
        user: str     = os.getenv("SMTP_USER", "")
        pw: str       = os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS", "")

        if not all([to_email, host, user, pw]):
            raise ValueError("Missing: EMAIL_TO, SMTP_HOST, SMTP_USER, or SMTP_PASSWORD")

        msg = httpx.Client().build_request(
            method="POST",
            url=f"https://api.mailgun.net/v1/{host}/messages",
            headers={"Authorization": f"Bearer {pw}"},
            data={
                "from": user,
                "to": [to_email],
                "subject": subject,
                "text": image_description
            },
            files=[("attachment", ("image.jpg", httpx.File(image_url), "image/jpeg"))]
        )

        resp = msg.send()
        if resp.status_code == 200:
            return {"status": "success", "summary": f"Email sent to {to_email}"}
        else:
            raise ValueError(f"Failed to send email: {resp.text}")

    except Exception as exc:
        return {"status": "error", "summary": str(exc)}
