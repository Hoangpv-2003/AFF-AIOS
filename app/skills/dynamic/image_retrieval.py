from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
import httpx


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    
    try:
        topic: str            = input_data.get("topic", "")
        data_source: str      = input_data.get("data_source", "")
        
        if not all([topic, data_source]):
            raise ValueError("'topic' and 'data_source' are required in input_data")

        url: str = f"https://api.tavily.com/search?query={topic}&include_images=True&max_results=5"
        api_key: str  = os.getenv("TAVILY_API_KEY", "")

        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable is not set")

        with httpx.Client(timeout=15) as client:
            resp = client.post(
                url,
                json={"api_key": api_key, "query": topic, 
                      "max_results": 5, "include_images": True},
            )
            resp.raise_for_status()

        data: dict             = resp.json()
        image_urls: List[str]  = data.get("images", [])
        results: List[dict]    = data.get("results", [])

        return {
            "status": "success",
            "image_urls": image_urls,
            "data": results,
            "summary": f"Found {len(results)} result(s) and {len(image_urls)} image(s) for '{topic}' from '{data_source}'",
        }
    except Exception as exc:
        return {"status": "error", "image_urls": [], "results": [], "summary": str(exc)}
