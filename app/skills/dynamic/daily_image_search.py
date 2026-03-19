from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
import httpx
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        data_source: str = input_data.get("data_source", "")

        if not data_source:
            raise ValueError("'data_source' is required in input_data")

        with httpx.Client(timeout=15) as client:
            resp = client.post(
                "https://api.tavily.com/search",
                json={"query": data_source, "max_results": 1},
            )
            resp.raise_for_status()

        data: dict = resp.json()
        image_urls: List[str] = data.get("images", [])
        results: List[dict]   = data.get("results", [])

        if not results:
            return {
                "status": "error",
                "image_url": "",
                "summary": f"No result found for '{data_source}'"
            }

        image_url: str = results[0].get("url", "")
        if not image_url:
            return {
                "status": "error",
                "image_url": "",
                "summary": f"Failed to retrieve image URL from Tavily API"
            }

        try:
            # Fetch the image
            resp_img = client.get(image_url)
            resp_img.raise_for_status()
            img_data: bytes = resp_img.content

            # Use BeautifulSoup for parsing
            soup = BeautifulSoup(img_data, 'html.parser')

            # Get the first <img> tag
            img_tag = soup.find('img')
            if img_tag:
                image_description: str = img_tag.get("alt", "")

            else:
                return {
                    "status": "error",
                    "image_url": "",
                    "summary": f"Failed to parse image description from Tavily API"
                }

        except Exception as exc:
            return {
                "status": "error",
                "image_url": "",
                "summary": str(exc)
            }

        # Encode image as base64
        img = Image.open(BytesIO(img_data))
        _, encoded_img = plt.imshow(img)

        return {
            "status": "success",
            "image_url": image_url,
            "image_description": image_description,
            "summary": f"Found a result for '{data_source}' and fetched the image"
        }

    except httpx.HTTPStatusError as exc:
        return {"status": "error", "image_url": "", "summary": f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"}
    except Exception as exc:
        return {"status": "error", "image_url": "", "summary": str(exc)}
