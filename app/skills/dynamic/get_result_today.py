from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
import httpx


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        query: str        = input_data.get("query", "")
        max_results: int  = int(input_data.get("max_results", 5))
        api_key: str      = os.getenv("SEARCH_API_KEY", "")

        if not query:
            raise ValueError("'query' is required in input_data")
        if not api_key:
            raise ValueError("SEARCH_API_KEY environment variable is not set")

        with httpx.Client(timeout=15) as client:
            resp = client.post(
                "https://search-api.com/search",
                json={"api_key": api_key, "query": query,
                      "max_results": max_results},
            )
            resp.raise_for_status()

        data: dict         = resp.json()
        result_list: List  = data.get("results", [])

        # Use a high-quality fallback URL if search image API call fails
        if not result_list:
            return {
                "status": "error",
                "result": [],
                "summary": f"Failed to fetch results for '{query}'. Using fallback URL.",
            }

        # Extract and store the first image URL in the list (if any)
        try:
            image_url: str = result_list[0].get("image_url", "")
            if not image_url.startswith("http"):
                raise ValueError("Invalid image URL")
        except IndexError:
            image_url = ""

        return {
            "status": "success",
            "result": result_list,
            "summary": f"Found {len(result_list)} results for '{query}'",
            "image_url": image_url if image_url else "",
        }
    except Exception as exc:
        return {"status": "error", "result": [], "summary": str(exc)}
