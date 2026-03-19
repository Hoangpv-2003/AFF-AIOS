from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt
from smtplib import SMTP
from email.message import EmailMessage

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        to_email: str  = input_data.get("to_email") or os.getenv("TO_EMAIL", "")
        subject: str   = "Random Image"
        description: str = ""
        
        if not all([to_email]):
            raise ValueError("Missing: to_email")

        with httpx.Client(timeout=15) as client:
            resp = client.get('https://picsum.photos/v2/list')
            resp.raise_for_status()

        data: dict = resp.json()
        image_url: str = data[0]['download_url']
        
        # Download the random image
        with httpx.Client(timeout=15) as client:
            resp = client.get(image_url)
            resp.raise_for_status()

        img_data: bytes = BytesIO(resp.content).read()
        img = Image.open(BytesIO(img_data))

        # Create a figure and axis
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Add the image to the axis
        ax.imshow(plt.imread(BytesIO(img_data)))
        
        # Set title and labels
        ax.set_title('Random Image')
        ax.axis('off')

        # Save the figure to a buffer
        buf = BytesIO()
        fig.savefig(buf, format="png")
        plt.close(fig)
        
        # Get the base64 encoded image
        img_base64: str = "data:image/png;base64," + buf.getvalue().decode("latin1")

        # Create an email message
        msg = EmailMessage()
        msg.set_content(description)
        msg.add_alternative("<img src=\"" + img_base64 + "\">", subtype="html")
        
        # Send the email
        host: str     = os.getenv("SMTP_HOST", "")
        port: int     = int(os.getenv("SMTP_PORT", "587"))
        user: str     = os.getenv("SMTP_USER", "")
        pw: str       = os.getenv("SMTP_PASS") or os.getenv("SMTP_PASSWORD", "")

        if not all([to_email, host, user, pw]):
            raise ValueError("Missing: to_email, SMTP_HOST, SMTP_USER, or SMTP_PASS")

        with SMTP(host, port) as smtp:
            smtp.starttls()
            smtp.login(user, pw)
            smtp.send_message(msg)

        return {
            "status": "success",
            "image_base64": img_base64,
            "description": description,
            "summary": f"Email sent to {to_email}",
        }
    except Exception as exc:
        return {"status": "error", "image_base64": "", "description": "", "summary": str(exc)}
