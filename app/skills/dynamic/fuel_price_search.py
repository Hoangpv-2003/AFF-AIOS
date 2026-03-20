from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        # Extract query from input data (will be used to search for fuel price data)
        query: str = input_data.get("query", "")

        # Set API key using environment variable
        api_key: str = os.getenv("TAVILY_API_KEY", "")

        if not query or not api_key:
            raise ValueError("'query' and TAVILY_API_KEY environment variable are required")

        with httpx.Client(timeout=15) as client:
            resp = client.post(
                "https://api.tavily.com/search",
                json={"api_key": api_key, "query": query,
                      "max_results": 10, "include_images": True},
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
