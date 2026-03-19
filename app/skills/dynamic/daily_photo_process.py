from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx
import smtplib
from email.message import EmailMessage
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import base64
import plotly.graph_objects as go

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    
    try:
        to_email: str = input_data.get("to_email", "")
        subject: str  = input_data.get("subject", "Daily Photo Summary")
        content: str  = ""
        
        if not to_email:
            raise ValueError("'to_email' is required in input_data")
        
        # Search for a random image using Tavily API
        query: str        = input_data.get("query", "")
        max_results: int  = int(input_data.get("max_results", 5))
        api_key: str      = os.getenv("TAVILY_API_KEY", "")

        if not query:
            raise ValueError("'query' is required in input_data")
        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable is not set")

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

        # Select the first image URL
        image_url: str = image_urls[0]

        # Download the image and extract its metadata
        with httpx.Client(timeout=15) as client:
            resp = client.get(image_url)
            resp.raise_for_status()

        img_data: bytes = resp.content

        # Encode the image as base64
        encoded_img: str = base64.b64encode(img_data).decode("utf-8")

        # Generate a plotly chart of the image
        fig = go.Figure(data=[go.Image(src=image_url)])
        plot_img: str = fig.to_image()

        # Create an email message with the summary and image
        msg = EmailMessage()
        msg.set_content(content)
        msg["Subject"] = subject
        msg["From"]    = to_email  # Assume this is set in environment variables
        msg["To"]      = to_email

        # Send the email using smtplib
        with smtplib.SMTP(os.getenv("SMTP_HOST", ""), int(os.getenv("SMTP_PORT", "587"))) as smtp:
            smtp.starttls()
            smtp.login(os.getenv("SMTP_USER", ""), os.getenv("SMTP_PASSWORD"))
            smtp.send_message(msg)

        return {
            "status": "success",
            "image_base64": encoded_img,
            "summary": f"Sent daily photo summary to {to_email}",
        }

    except Exception as exc:
        return {"status": "error", "image_base64": "", "summary": str(exc)}
