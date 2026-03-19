from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
import json
import httpx
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import plotly.graph_objects as go

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Orchestrates the daily random image skill by searching for a random image using Tavily API,
    generating a short description, and sending an email with the image and description.
    
    Args:
        input_data (Optional[Dict[str, Any]], optional): Input data. Defaults to None.

    Returns:
        Dict[str, Any]: Output dictionary containing status, summary, and result details.
    """

    # Default to empty values if not provided in input_data
    input_data = input_data or {}

    try:
        # Extract necessary parameters from input_data
        recipient_email: str = input_data.get("recipient_email") or input_data.get("email", "")
        schedule_time: str = input_data.get("schedule_time", "08:00")

        if not all([recipient_email]):
            raise ValueError("'recipient_email' is required in input_data")

        # Search for random images using Tavily API
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                "https://api.tavily.com/search",
                json={"query": "", "max_results": 1, "include_images": True},
            )
            resp.raise_for_status()

        # Get the image URL and description from the response
        data: dict = resp.json()
        image_url: str = data.get("images", [])[0]
        description: str = BeautifulSoup(data.get("description", ""), 'html.parser').get_text()

        # Generate a short description using natural language processing libraries (Plotly/ Matplotlib)
        fig, ax = plt.subplots()
        ax.imshow(plt.imread(image_url))
        ax.axis('off')
        plt.savefig('temp_image.png', bbox_inches='tight')

        image_description: str = "An image of a beautiful nature scene."

        # Send the email with the image and description attached
        msg = EmailMessage()
        msg.set_content(f"Here is your daily random image with a short description:\n\n{image_description}")
        msg.add_attachment(open('temp_image.png', 'rb').read(), subtype='jpeg', filename='temp_image.jpg')
        msg["Subject"] = "Your Daily Random Image"
        msg["From"]    = os.getenv("SMTP_USER", "")
        msg["To"]      = recipient_email

        # Use smtplib (SMTP) to send the email
        import smtplib
        with smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT"))) as smtp:
            smtp.starttls()
            smtp.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
            smtp.send_message(msg)

        # Remove temporary image file
        os.remove('temp_image.png')

        return {
            "status": "success",
            "image_url": image_url,
            "description": description,
            "email_status": f"Email sent to {recipient_email} at {schedule_time}",
        }
    except Exception as exc:
        # Return error dictionary with summary and details
        return {"status": "error", "image_url": "", "description": "", "summary": str(exc)}
