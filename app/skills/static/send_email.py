from __future__ import annotations
from typing import Any, Dict, Optional
import httpx
from bs4 import BeautifulSoup
import json


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        to_email: str = input_data.get("to_email")  # type: ignore
        subject: str  = input_data.get("subject", "Notification from AIOS")
        content: str  = input_data.get("content", "")
        image_url: str = input_data.get("image_url", "")

        if not all([to_email, content]):
            raise ValueError("Missing: to_email or content")

        # Fetch image URL
        if image_url:
            with httpx.Client(timeout=10) as client:
                try:
                    res = client.get(image_url)
                    res.raise_for_status()
                except Exception as exc:
                    return {"status": "error", "summary": str(exc)}

                # Extract base64 encoded image from response
                soup = BeautifulSoup(res.text, 'html.parser')
                img_tags = soup.find_all('img')

                if not img_tags:
                    raise ValueError("No images found in the HTML")

                image_base64 = ''
                for tag in img_tags:
                    if tag.get('src'):
                        try:
                            with httpx.Client(timeout=10) as client:
                                res_img = client.get(tag['src'])
                                res_img.raise_for_status()
                                image_base64 += res_img.text
                        except Exception as exc:
                            return {"status": "error", "summary": str(exc)}

                # Send email
                msg = httpx.Request("POST", "https://httpbin.org/email")
                msg.headers["Content-Type"] = "text/plain"
                msg.body = f"Subject: {subject}\n\n{content}"
                if image_base64:
                    msg.body += "\n\nImage:\n" + image_base64
                resp = httpx.send(msg)
                resp.raise_for_status()

                return {"status": "success", "summary": f"Email sent to {to_email}"}
        else:
            # Send email without image
            msg = httpx.Request("POST", "https://httpbin.org/email")
            msg.headers["Content-Type"] = "text/plain"
            msg.body = f"Subject: {subject}\n\n{content}"
            resp = httpx.send(msg)
            resp.raise_for_status()

            return {"status": "success", "summary": f"Email sent to {to_email}"}
    except Exception as exc:
        return {"status": "error", "summary": str(exc)}
