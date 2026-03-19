from __future__ import annotations
from typing import Any, Dict, Optional
import httpx
import pandas as pd  # Not used in this version, but imported to follow coder_notes
import smtplib  # Allowed by feedback from CodeReviewer
import email.message  # For EmailMessage class

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    
    try:
        topic: str = input_data.get("topic", "")
        facts_to_remember: List[str] = input_data.get("facts_to_remember", [])
        
        if not topic:
            raise ValueError("'topic' is required in input_data")
        
        # Fetch latest scores using httpx
        url: str = "https://example.com/latest-scores"
        headers: dict = {"Authorization": f"Bearer {os.getenv('API_KEY', '')}"}
        payload: dict = {}
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, headers=headers, params=payload)
            resp.raise_for_status()
        
        scores_data: dict = resp.json()
        
        # Process data using pandas (not used in this version)
        # pd.DataFrame(scores_data).to_csv("scores.csv", index=False)
        
        # Send email using smtplib
        to_email: str = os.getenv('SMTP_TO_EMAIL', '')
        subject: str = f"DAILY FOOTBALL WORKFLOW - {topic}"
        content: str = ""
        for fact in facts_to_remember:
            content += f"- {fact}\n"
        
        host: str     = os.getenv("SMTP_HOST", "")
        port: int     = int(os.getenv("SMTP_PORT", "465"))
        user: str     = os.getenv("SMTP_USER", "")
        pw: str       = os.getenv("SMTP_PASS") or os.getenv("SMTP_PASSWORD", "")

        if not all([to_email, host, user, pw]):
            raise ValueError("Missing: to_email, SMTP_HOST, SMTP_USER, or SMTP_PASS")

        msg = email.message.EmailMessage()
        msg.set_content(content)
        msg["Subject"] = subject
        msg["From"]    = user
        msg["To"]      = to_email

        # Attach image via Base64 (from local chart generation)
        # img_b64 = input_data.get("image_base64", "")
        # if img_b64:
        #     ...

        # Automatically download and attach image if url is provided
        # image_url: str = input_data.get("image_url", "")
        # with httpx.Client(timeout=10) as client:
        #     res = client.get(image_url)
        #     if res.status_code == 200:
        #         ...

        with smtplib.SMTP_SSL(host, port) as smtp:
            smtp.login(user, pw)
            smtp.send_message(msg)

        return {
            "status": "success",
            "summary": f"Email sent to {to_email}",
            "next_action": "Wait for next day's scores"
        }
    except Exception as exc:
        return {"status": "error", "summary": str(exc)}
