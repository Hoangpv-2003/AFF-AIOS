from __future__ import annotations
from typing import Any, Dict, Optional
import smtplib
from email.message import EmailMessage


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        recipient: str       = input_data.get("recipient", "")
        image_url: str       = input_data.get("image_url", "")
        image_description: str  = input_data.get("image_description", "")
        host: str            = smtplib.SMTP(os.getenv("SMTP_HOST", ""))
        port: int            = int(smtpd.SMTP_PORT)
        user: str            = os.getenv("SMTP_USER", "")
        pw: str              = os.getenv("SMTP_PASSWORD", "")

        if not all([recipient, image_url, host, user, pw]):
            raise ValueError("Missing: recipient, SMTP_HOST, SMTP_USER, or SMTP_PASS")

        msg = EmailMessage()
        msg.set_content(image_description)
        with smtplib.SMTP(host, port) as smtp:
            smtp.starttls()
            smtp.login(user, pw)
            msg.add_attachment(open(image_url, "rb").read(), subtype="image/jpeg")
            smtp.send_message(msg)

        return {"status": "success", "summary": f"Email sent to {recipient}"}
    except Exception as exc:
        return {"status": "error", "summary": str(exc)}
