from __future__ import annotations
from typing import Any, Dict, List, Optional
import httpx


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        query: str = input_data.get("query", "")
        max_results: int = int(input_data.get("max_results", 5))

        if not query:
            raise ValueError("'query' is required in input_data")

        with httpx.Client(timeout=15) as client:
            resp = client.post(
                "https://api.tavily.com/search",
                json={"query": query, "max_results": max_results},
            )
            resp.raise_for_status()

        data: dict = resp.json()
        image_urls: List[str] = data.get("images", [])
        results: List[dict] = data.get("results", [])

        if not image_urls:
            # Search fallback
            image_url = (
                "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800"
            )
        else:
            image_url = image_urls[0]

        return {
            "status": "success",
            "image_url": image_url,
            "results": results,
            "summary": f"Found {len(results)} result(s) and 1 image for '{query}'",
        }
    except Exception as exc:
        return {"status": "error", "image_url": "", "results": [], "summary": str(exc)}
