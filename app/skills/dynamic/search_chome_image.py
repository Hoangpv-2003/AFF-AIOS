from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        api_key: str      = os.getenv("TAVILY_API_KEY", "")
        query: str        = input_data.get("query", "")

        if not api_key or not query:
            raise ValueError("'api_key' and 'query' are required")

        with httpx.Client(timeout=15) as client:
            resp = client.post(
                "https://api.tavily.com/search",
                json={"api_key": api_key, "query": query,
                      "max_results": 5, "include_images": True},
            )
            resp.raise_for_status()

        data: dict            = resp.json()
        image_urls: List[str] = data.get("images", [])
        results: List[dict]   = data.get("results", [])

        # Fallback search if Tavily API fails
        if not image_urls:
            image_url = "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800"  # fallback nature URL
            return {
                "status": "success",
                "image_urls": [image_url],
                "results": results,
                "summary": f"No results from Tavily, using fallback image for '{query}'",
            }

        return {
            "status": "success",
            "image_urls": image_urls,
            "results": results,
            "summary": f"Found {len(results)} result(s) and {len(image_urls)} image(s) for '{query}'",
        }
    except httpx.HTTPStatusError as exc:
        return {"status": "error", "image_urls": [], "results": [], "summary": f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"}
    except Exception as exc:
        return {"status": "error", "image_urls": [], "results": [], "summary": str(exc)}
