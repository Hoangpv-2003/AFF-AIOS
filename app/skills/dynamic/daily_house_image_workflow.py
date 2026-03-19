from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
import httpx
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        query: str = input_data.get("query", "")
        
        if not query:
            raise ValueError("'query' is required in input_data")

        with httpx.Client(timeout=15) as client:
            resp = client.post(
                "https://api.tavily.com/search",
                json={"api_key": os.getenv("TAVILY_API_KEY", ""),
                      "query": query,
                      "max_results": 1, "include_images": True},
            )
            resp.raise_for_status()

        data: dict            = resp.json()
        image_urls: List[str] = [item["url"] for item in data.get("images", [])]
        results: List[dict]   = data.get("results", [])

        # Parse JSON response to extract image URL and description
        img_url = image_urls[0]
        result  = results[0]

        # Use BeautifulSoup to parse HTML content of the webpage with the image
        html_text = httpx.get(img_url).text
        soup      = BeautifulSoup(html_text, 'html.parser')
        
        # Extract title from the webpage
        title: str = soup.title.text

        # Use matplotlib to generate chart (not needed in this case)
        plt.imshow(plt.imread(img_url))
        plt.axis('off')

        # Encode PNG as base64 and store in 'image_base64' key
        image_base64: str = plt.tostring(plt.gcf(), format='raw_image').decode()
        
        return {
            "status": "success",
            "image_base64": image_base64,
            "description": title[:200],  # safely truncate to 200 characters
            "summary": f"Found an image for '{query}' and sent it via email",
        }
    except Exception as exc:
        return {"status": "error", "image_base64": "", "description": "", "summary": str(exc)}
