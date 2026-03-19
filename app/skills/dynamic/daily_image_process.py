from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
import httpx
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt
from base64 import b64encode

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        image_url: str  = input_data.get("image_url", "")
        description: str = input_data.get("image_description", "")

        if not image_url:
            raise ValueError("'image_url' is required in input_data")
        
        with httpx.Client(timeout=15) as client:
            resp = client.get(image_url)
            resp.raise_for_status()

        img_bytes = BytesIO(resp.content)

        # parse the HTML content of the image URL
        soup = BeautifulSoup(img_bytes.read(), 'html.parser')
        img_tag = soup.find('img')

        if not img_tag:
            raise ValueError("Failed to find image tag in response")

        image_base64: str = b64encode(resp.content).decode('utf-8')
        
        return {
            "status": "success",
            "image_base64": [image_base64],
            "summary": f"Retrieved and processed {image_url} with description '{description}'"
        }
    except Exception as exc:
        return {"status": "error", "image_base64": [], "summary": str(exc)}
