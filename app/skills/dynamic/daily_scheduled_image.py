from __future__ import annotations
from typing import Any, Dict, Optional
import os
import json
import httpx
import matplotlib.pyplot as plt
from email.message import EmailMessage
from bs4 import BeautifulSoup
import smtplib

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    
    # Define constants and get environment variables
    base_url = os.getenv("BASE_URL", "https://unsplash.com")
    api_key = os.getenv("UNSPASH_API_KEY", "")
    
    # Set defaults for input parameters
    query: str        = input_data.get("query", "mountain")
    max_results: int  = int(input_data.get("max_results", 1))
    email_to: str     = input_data.get("email", "")
    description: str  = input_data.get("description", "")

    # Validate environment variables
    if not api_key:
        raise ValueError("UNSPASH_API_KEY environment variable is not set")
    if not email_to:
        raise ValueError("'email' is required in input_data")

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(f"{base_url}/search/photos", params={"query": query, "orientation": "landscape"})
            resp.raise_for_status()

        data: dict = resp.json()
        
        image_urls: List[str] = []
        results: List[dict]   = []

        # Iterate over search results and extract image URLs
        for item in data.get("results", []):
            try:
                image_url: str = item["urls"]["full"]
                image_urls.append(image_url)
                results.append(item)
            except Exception as exc:
                print(f"Error processing item {item}: {str(exc)}")
        
        # Send email with selected image and description
        msg = EmailMessage()
        msg.set_content(description)
        msg["Subject"] = f"Hình ảnh ngẫu nhiên - {query}"
        msg["From"]    = "your-email@gmail.com"
        msg["To"]      = email_to

        img_url: str = image_urls[0]
        response = httpx.get(img_url, timeout=15)
        with open("image.jpg", "wb") as f:
            f.write(response.content)

        plt.imshow(plt.imread("image.jpg"))
        plt.axis('off')
        plt.savefig("image.png")
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login("your-email@gmail.com", "password")
            with open("image.png", "rb") as f:
                content = f.read()
            msg.add_attachment(content, maintype="image", subtype="png")
            smtp.send_message(msg)

        return {
            "status": "success",
            "summary": f"Sent image to {email_to}",
        }
    except httpx.HTTPStatusError as exc:
        return {"status": "error", "data": {}, "summary": f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"}
    except Exception as exc:
        return {"status": "error", "data": {}, "summary": str(exc)}
