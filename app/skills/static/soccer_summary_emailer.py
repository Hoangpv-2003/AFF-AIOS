from __future__ import annotations
from typing import Any, Dict, Optional
import os
import smtplib
from email.message import EmailMessage


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        to_email: str = input_data.get("to_email") or input_data.get("email", "")
        subject: str  = input_data.get("subject", "Soccer Summary")
        content: str  = input_data.get("content", "")
        summary: str  = input_data.get("summary", "")

        if not all([to_email, subject, content]):
            raise ValueError("Missing: to_email, subject or content")

        msg = EmailMessage()
        msg.set_content(content)
        msg["Subject"] = subject
        msg["From"]    = os.getenv("SMTP_USER", "")
        msg["To"]      = to_email

        with smtplib.SMTP(os.getenv("SMTP_HOST", ""), int(os.getenv("SMTP_PORT", "587"))) as smtp:
            smtp.starttls()
            smtp.login(os.getenv("SMTP_USER", ""), os.getenv("SMTP_PASSWORD", ""))
            smtp.send_message(msg)

        return {
            "status": "success",
            "summary": f"Email sent to {to_email}",
        }
    except Exception as exc:
        return {"status": "error", "summary": str(exc)}
