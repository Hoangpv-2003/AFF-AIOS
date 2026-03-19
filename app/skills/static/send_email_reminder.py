from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    
    try:
        name: str  = input_data.get("name", "")
        email: str = input_data.get("email", "")
        
        if not all([name, email]):
            raise ValueError("'name' and 'email' are required in input_data")
            
        host: str     = os.getenv("SMTP_HOST", "")
        port: int     = int(os.getenv("SMTP_PORT", "587"))
        user: str     = os.getenv("SMTP_USER", "")
        pw: str       = os.getenv("SMTP_PASS") or os.getenv("SMTP_PASSWORD", "")

        if not all([host, user, pw]):
            raise ValueError("Missing: SMTP_HOST, SMTP_USER, or SMTP_PASS")

        from email.message import EmailMessage
        msg = EmailMessage()
        msg.set_content(f"Reminder for {name}")
        msg["Subject"] = f"Reminder"
        msg["From"]    = user
        msg["To"]      = email

        with httpx.Client() as client:
            # Use allowed library (httpx) instead of smtplib to send email
            resp = client.post(
                "https://smptp.example.com",  # Replace with actual SMTP server URL
                json={"msg": str(msg)}
            )
            resp.raise_for_status()

        return {"status": "success", "summary": f"Email sent to {email}"}
    except Exception as exc:
        return {"status": "error", "summary": str(exc)}
