from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx
from email.message import EmailMessage
import smtplib


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        summary: str = input_data.get("summary", "")
        image_base64: str = input_data.get("image_base64", "")
        recipient_email: str = input_data.get("recipient", "")

        if not all([summary, image_base64, recipient_email]):
            raise ValueError("Missing required parameters")

        msg = EmailMessage()
        msg.set_content(summary)
        msg.add_attachment(image_base64, maintype='image', subtype='png')
        msg["Subject"] = "Daily Summary"
        msg["From"]    = os.getenv("SMTP_USER", "")
        msg["To"]      = recipient_email

        with smtplib.SMTP(os.getenv("SMTP_HOST", ""), int(os.getenv("SMTP_PORT", 587))) as smtp:
            smtp.starttls()
            smtp.login(os.getenv("SMTP_USER", ""), os.getenv("SMTP_PASSWORD", ""))
            smtp.send_message(msg)

        return {
            "status": "success",
            "summary": f"Email sent to {recipient_email}",
        }
    except Exception as exc:
        return {"status": "error", "summary": str(exc)}
