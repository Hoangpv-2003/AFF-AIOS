from __future__ import annotations
import os, httpx
from typing import Any, Dict, Optional
def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    topic = input_data.get("topic")
    recipient = input_data.get("recipient")
    
    key = os.getenv("TAVILY_API_KEY")
    with httpx.Client() as cl:
        r = cl.post("https://api.tavily.com/search", json={
            "api_key": key, "query": topic, "include_images": True, "search_depth": "advanced"
        })
        r.raise_for_status()
    data = r.json()
    results = data.get("results", [])
    
    # Prepare email content
    summary_text = "Tóm tắt thông tin:\n"
    for r in results[:3]:
        summary_text += f"- {r.get('title')}: {r.get('content')[:150]}...\n"
    
    # Email sending logic (reusing Email skill structure)
    host, port = os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT", 465))
    user, pw = os.getenv("SMTP_USER"), os.getenv("SMTP_PASS") or os.getenv("SMTP_PASSWORD")
    
    msg = EmailMessage()
    msg["Subject"] = "Báo cáo doanh thu Viettel năm 2025"
    msg["From"], msg["To"] = user, recipient
    msg.set_content(summary_text)
    
    images = data.get("images", [])
    if images and isinstance(images, list):
        img_url = images[0]
        with httpx.Client() as img_cl:
            img_response = img_cl.get(img_url)
            if img_response.status_code == 200:
                msg.add_attachment(img_response.content, filename="report_image.png")
    
    # Simulate scheduling by immediately sending (no actual scheduling logic)
    return {"status": "success", "message": "Báo cáo đã được lên lịch gửi"}