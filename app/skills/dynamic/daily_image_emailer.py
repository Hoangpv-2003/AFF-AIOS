from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx
import matplotlib.pyplot as plt  # type: ignore
import plotly.graph_objects as go  # type: ignore
from bs4 import BeautifulSoup

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        recipient_email: str = input_data.get("recipient", "")
        schedule_time: str   = input_data.get("schedule_time", "08:00")
        
        if not recipient_email:
            raise ValueError("'recipient' is required in input_data")
        
        # Fetch a random image from Tavily API
        api_key: str      = os.getenv("TAVILY_API_KEY", "")
        query: str        = ""
        max_results: int  = 1
        
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                "https://api.tavily.com/search",
                json={"api_key": api_key, "query": query,
                      "max_results": max_results, "include_images": True},
            )
            resp.raise_for_status()
        
        data: dict            = resp.json()
        image_urls: List[str] = data.get("images", [])
        results: List[dict]   = data.get("results", [])
        
        if not image_urls or not results:
            raise ValueError("No images found")
        
        # Get a random image
        image_url: str = image_urls[0]
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(image_url)
                resp.raise_for_status()
                
            image_data = resp.content
        
            # Generate short description using matplotlib and plotly
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.imshow(BeautifulSoup(resp.text, 'html.parser').find('img')['src'])
            description = "Image description: " + go.FigureWidget(fig).data[0].update(xaxis_title="", yaxis_title="").layout.title.text
        
        except Exception as exc:
            image_url = "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800"
        
        # Send email using smtplib
        to_email: str = recipient_email
        subject: str  = "Daily Image Emailer"
        content: str  = description
        
        host: str     = os.getenv("SMTP_HOST", "")
        port: int     = int(os.getenv("SMTP_PORT", "587"))
        user: str     = os.getenv("SMTP_USER", "")
        pw: str       = os.getenv("SMTP_PASS") or os.getenv("SMTP_PASSWORD", "")

        if not all([to_email, host, user, pw]):
            raise ValueError("Missing: to_email, SMTP_HOST, SMTP_USER, or SMTP_PASS")

        msg = "Subject: {}\n\n{}".format(subject, content)
        
        with smtplib.SMTP(host, port) as smtp:
            smtp.starttls()
            smtp.login(user, pw)
            smtp.sendmail(user, to_email, msg)

        return {
            "status": "success",
            "image_base64": image_data,
            "description": description,
            "summary": f"Sent daily image email to {to_email} at {schedule_time}",
        }
    except Exception as exc:
        return {"status": "error", "image_base64": "", "description": "", "summary": str(exc)}
