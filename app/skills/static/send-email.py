from __future__ import annotations
import os, smtplib, httpx
from email.message import EmailMessage
from typing import Any, Dict, Optional
def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    to = input_data.get("recipient")
    data = input_data.get("results")
    
    msg = EmailMessage()
    msg["Subject"] = "AAF-AIOS Professional Report"
    msg["From"], msg["To"] = os.getenv("SMTP_USER"), to

    # Generate summary from Tavily results
    summary_text = "Tóm tắt thông tin:\n"
    for r in data.get("results", [])[:3]:
        summary_text += f"- {r.get('title')}: {r.get('content')[:150]}...\n"
    msg.set_content(summary_text)
    
    # Attach images from Tavily results
    images = data.get("images", [])
    for img in images:
        if img.get("url") and img.get("content"):
            try:
                with httpx.Client() as cl:
                    resp = cl.get(img["url"], timeout=15)
                    if resp.status_code == 200:
                        msg.add_attachment(
                            resp.content, 
                            maintype='image', 
                            subtype='jpeg', 
                            filename=img.get("filename", "attachment.jpg")
                        )
            except: pass

    # SMTP SSL configuration
    host, port = os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT", 465))
    user, pw = os.getenv("SMTP_USER"), os.getenv("SMTP_PASS") or os.getenv("SMTP_PASSWORD")
    
    if port == 465:
        with smtplib.SMTP_SSL(host, port) as s:
            s.login(user, pw)
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, port) as s:
            s.starttls()
            s.login(user, pw)
            s.send_message(msg)
    return {"status": "success", "summary": "sent professional email"}