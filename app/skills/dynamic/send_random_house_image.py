from __future__ import annotations
from typing import Any, Dict, Optional
import httpx
import json
import requests

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        url: str      = input_data.get("house_image_url", "")
        recipient_email: str  = input_data.get("recipient_email", "")

        if not all([url, recipient_email]):
            raise ValueError("'house_image_url' and 'recipient_email' are required in input_data")

        # Use a safe fallback URL for image search
        search_fallback_url: str = "https://images.unsplash.com/photo-1449034446853-66c86144b0ad?w=800"

        with httpx.Client(timeout=15) as client:
            resp = client.get(url)
            resp.raise_for_status()

            data: dict = resp.json()
            image_urls: List[str] = data.get("images", [])

            # Get the first image URL
            image_url: str = image_urls[0]

        # Send Email
        subject: str  = "Random House Image"
        content: str  = f"Here's a random house image for you."
        image_base64: str = ""

        if image_url != search_fallback_url:
            try:
                res = requests.get(image_url)
                image_data = res.content
                maintype, subtype = from_bytes_to_mimetype(res.content[:20])
                image_base64 = "data:image/" + maintype.lower() + ";base64," + image_data.decode('latin1')
            except Exception as exc:
                print(f"Error converting image URL to base64: {exc}")

        msg = EmailMessage()
        msg.set_content(content or "Please see the attached content.")
        msg["Subject"] = subject
        msg["From"]    = "aios@domain.com"
        msg["To"]      = recipient_email

        # Automatically download and attach image if url is provided
        if image_url != search_fallback_url:
            msg.add_attachment(image_data, maintype=maintype, subtype=subtype, filename=f"attachment.{maintype}")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login("aios@domain.com", "password")
            smtp.send_message(msg)

        return {
            "status": "success",
            "image_base64": image_base64,
            "email_status": "Email sent to " + recipient_email,
            "summary": f"Random house image sent to {recipient_email}",
        }
    except Exception as exc:
        return {"status": "error", "image_base64": "", "email_status": "", "summary": str(exc)}

def from_bytes_to_mimetype(b: bytes) -> (str, str):
    extension_map = {
        b'\xff\xd8\xff\xe0': 'jpg',
        b'\x89\x50\x4e\x47': 'png'
    }
    for ext in extension_map:
        if b.startswith(ext):
            return extension_map[ext], extension_map[ext]
