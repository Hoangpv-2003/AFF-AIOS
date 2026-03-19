from __future__ import annotations
from typing import Any, Dict, Optional
import smtplib
from email.message import EmailMessage
import httpx


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Sends an email to tuanm7530@gmail.com with content related to VinFast logo.

    Args:
        input_data (Optional[Dict[str, Any]], optional): Input data for the skill. Defaults to None.

    Returns:
        Dict[str, Any]: A dictionary containing the status and summary of the skill's execution.
    """

    input_data = input_data or {}
    try:
        vinfast_logo_info: dict = input_data.get("vinfast_logo_info", {})
        tuanm7530_email: str = "tuanm7530@gmail.com"
        
        host: str     = os.getenv("SMTP_HOST", "")
        port: int     = int(os.getenv("SMTP_PORT", "465"))
        user: str     = os.getenv("SMTP_USER", "")
        pw: str       = os.getenv("SMTP_PASS") or os.getenv("SMTP_PASSWORD", "")

        if not all([tuanm7530_email, host, user, pw]):
            raise ValueError("Missing: tuanm7530_email, SMTP_HOST, SMTP_USER, or SMTP_PASS")

        msg = EmailMessage()
        msg.set_content(vinfast_logo_info.get("description", ""))
        msg["Subject"] = vinfast_logo_info.get("name", "VinFast Logo")
        msg["From"]    = user
        msg["To"]      = tuanm7530_email

        # Automatically download and attach image if url is provided
        if "url" in vinfast_logo_info:
            with httpx.Client(timeout=10) as client:
                res = client.get(vinfast_logo_info["url"])
                if res.status_code == 200:
                    image_data = res.content
                    maintype = "image"
                    subtype = "jpeg" # default
                    if "png" in vinfast_logo_info["url"].lower(): subtype = "png"
                    msg.add_attachment(image_data, maintype=maintype, subtype=subtype, filename=f"attachment.{subtype}")

        # Send Email
        if port == 465:
            with smtplib.SMTP_SSL(host, port) as smtp:
                smtp.login(user, pw)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host, port) as smtp:
                smtp.starttls()
                smtp.login(user, pw)
                smtp.send_message(msg)

        return {
            "status": "success",
            "email_sent_status": True,
            "email_contents": vinfast_logo_info.get("description", ""),
            "summary": f"Email sent to {tuanm7530_email}",
        }
    except Exception as exc:
        return {"status": "error", "email_sent_status": False, "email_contents": "", "summary": str(exc)}
