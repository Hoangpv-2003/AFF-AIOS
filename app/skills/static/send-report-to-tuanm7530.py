from __future__ import annotations
import os, smtplib, httpx
from email.message import EmailMessage
from typing import Any, Dict, Optional
def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    to = input_data.get("recipient")
    results = input_data.get("results")
    
    # Generate summary from search results
    summary_text = "Tóm tắt thông tin:\n"
    for r in results[:3]:
        summary_text += f"- {r.get('title')}: {r.get('content')[:150]}...\n"
    
    # Extract images from search results
    images = [img for img in results if img.get("type") == "image"]
    img_url = images[0]["image_url"] if images else None

    host, port = os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT", 465))
    user, pw = os.getenv("SMTP_USER"), os.getenv("SMTP_PASS") or os.getenv("SMTP_PASSWORD")
    
    msg = EmailMessage()
    msg["Subject"] = "Báo cáo doanh thu VinFast 2025"
    msg["From"], msg["To"] = user, to
    
    msg.set_content(summary_text)
    
    if img_url and img_url.startswith("http"):
        try:
            with httpx.Client() as cl:
                resp = cl.get(img_url, timeout=15)
                if resp.status_code == 200:
                    msg.add_attachment(resp.content, maintype='image', subtype='jpeg', filename='attachment.jpg')
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
    return {"status": "success", "summary": "sent report to tuanm7530@gmail.com"}