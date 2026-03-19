from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        query: str        = input_data.get("query", "")
        max_results: int  = int(input_data.get("max_results", 5))
        api_key: str      = os.getenv("TAVILY_API_KEY", "")

        if not query:
            raise ValueError("'query' is required in input_data")
        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable is not set")

        with httpx.Client(timeout=15) as client:
            resp = client.post(
                "https://api.tavily.com/search",
                json={"api_key": api_key, "query": query,
                      "max_results": max_results, "include_images": True},
            )
            resp.raise_for_status()

        data: dict            = resp.json()
        image_urls: List[str] = data.get("images", [])
        results: List[dict]   = data.get("results", [])

        return {
            "status": "success",
            "image_urls": image_urls,
            "results": results,
            "summary": f"Found {len(results)} result(s) and {len(image_urls)} image(s) for '{query}'",
        }
    except Exception as exc:
        return {"status": "error", "image_urls": [], "results": [], "summary": str(exc)}
