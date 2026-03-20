from __future__ import annotations
import os, smtplib, httpx
from email.message import EmailMessage
from typing import Any, Dict, Optional
def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    to = input_data.get("recipient")
    host, port = os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT", 465))
    user, pw = os.getenv("SMTP_USER"), os.getenv("SMTP_PASS") or os.getenv("SMTP_PASSWORD")
    
    msg = EmailMessage()
    msg["Subject"] = "Hình ảnh con mèo đẹp"
    msg["From"], msg["To"] = user, to

    summary = "Dưới đây là hình ảnh con mèo đẹp mà chúng tôi tìm được:"
    msg.set_content(summary)
    
    results = input_data.get("results", [])
    if results:
        img_url = results[0].get("url")
        if img_url and img_url.startswith("http"):
            try:
                with httpx.Client() as cl:
                    resp = cl.get(img_url, timeout=15)
                    if resp.status_code == 200:
                        msg.add_attachment(resp.content, maintype='image', subtype='jpeg', filename='cat.jpg')
            except: pass

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