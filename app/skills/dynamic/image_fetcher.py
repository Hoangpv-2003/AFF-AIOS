from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx
from bs4 import BeautifulSoup


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        topic: str      = input_data.get("topic", "")
        data_source: str = input_data.get("data_source", "")

        if not all([topic, data_source]):
            raise ValueError("'topic' and 'data_source' are required in input_data")

        api_key: str  = os.environ.get('TAVILY_API_KEY')
        url: str      = f"https://api.tavily.com/search?api_key={api_key}&query={topic}&include_images=true&max_results=1"
        response: httpx.Response = httpx.get(url)

        if response.status_code == 200:
            data: dict = response.json()
            image_url: str = data["images"][0]
            description: str = BeautifulSoup(data["results"][0]["html"], 'html.parser').get_text()

            return {
                "status": "success",
                "image_url": image_url,
                "description": description,
                "summary": f"Found {topic} with URL: {image_url}",
            }
        else:
            return {"status": "error", "image_url": "", "description": "", "summary": f"Failed to fetch data for topic {topic}"}
    except Exception as exc:
        return {"status": "error", "image_url": "", "description": "", "summary": str(exc)}
