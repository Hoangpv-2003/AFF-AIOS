from __future__ import annotations
from typing import Any, Dict, Optional
import smtplib
from email.message import EmailMessage
import httpx


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        image_url: str   = input_data.get("image_url", "")
        to_email: str    = input_data.get("to_email", "")
        subject: str     = input_data.get("subject", "Notification from AIOS")
        content: str     = input_data.get("content", "")

        if not all([image_url, to_email]):
            raise ValueError("'image_url' and 'to_email' are required in input_data")

        msg = EmailMessage()
        msg.set_content(content or "Please see the attached image.")
        msg["Subject"] = subject
        msg["From"]    = "your-email@gmail.com"
        msg["To"]      = to_email

        # Automatically download and attach image if url is provided
        with httpx.Client(timeout=10) as client:
            res = client.get(image_url)
            if res.status_code == 200:
                image_data = res.content
                maintype = "image"
                subtype = "jpeg" # default
                if "png" in image_url.lower(): subtype = "png"
                msg.add_attachment(image_data, maintype=maintype, subtype=subtype, filename=f"attachment.{subtype}")

        # Send Email
        host: str     = "your-smtp-host"
        port: int     = 587
        user: str     = "your-smtp-username"
        pw: str       = "your-smtp-password"

        if not all([host, user, pw]):
            raise ValueError("Missing SMTP credentials")

        with smtplib.SMTP(host, port) as smtp:
            smtp.starttls()
            smtp.login(user, pw)
            smtp.send_message(msg)

        return {"status": "success", "summary": f"Email sent to {to_email}"}
    except Exception as exc:
        return {"status": "error", "summary": str(exc)}
