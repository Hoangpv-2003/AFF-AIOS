from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
import smtplib
from email.message import EmailMessage
import httpx


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Send dog and cat images via email.
    
    This skill uses the `smtplib` library to connect to an SMTP server,
    authenticate with a username and password, and send an email containing
    images of dogs and cats.

    Args:
        input_data (Optional[Dict[str, Any]]): A dictionary containing the image URLs
            that will be sent via email. If None, it defaults to an empty dictionary.
    
    Returns:
        Dict[str, Any]: A dictionary with two keys: "status" and "summary".
            The value of "status" is either "success" or "error", depending on whether
            the email was successfully sent. The value of "summary" is a string that
            provides additional information about what happened during the execution of this skill.
    """

    input_data = input_data or {}
    
    try:
        # Get image URLs from input data
        image_urls: List[str] = input_data.get("image_urls", [])
        
        if not image_urls:
            raise ValueError("'image_urls' is required in input_data")
        
        to_email: str = input_data.get("to_email") or input_data.get("email", "")
        subject: str  = input_data.get("subject", "Notification from AIOS")
        content: str  = input_data.get("content", "")

        host: str     = os.getenv("SMTP_HOST", "")
        port: int     = int(os.getenv("SMTP_PORT", "465"))
        user: str     = os.getenv("SMTP_USER", "")
        pw: str       = os.getenv("SMTP_PASS") or os.getenv("SMTP_PASSWORD", "")

        if not all([to_email, host, user, pw]):
            raise ValueError("Missing: to_email, SMTP_HOST, SMTP_USER, or SMTP_PASS")

        # Create email message
        msg = EmailMessage()
        msg.set_content(content)
        msg["Subject"] = subject
        msg["From"]    = user
        msg["To"]      = to_email

        # Attach image via URL
        for image_url in image_urls:
            with httpx.Client(timeout=10) as client:
                res = client.get(image_url)
                if res.status_code == 200:
                    image_data = res.content
                    maintype = "image"
                    subtype = "jpeg" # default
                    if "png" in image_url.lower(): subtype = "png"
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

        return {"status": "success", "summary": f"Email sent to {to_email}"}
    
    except Exception as exc:
        return {"status": "error", "summary": str(exc)}
