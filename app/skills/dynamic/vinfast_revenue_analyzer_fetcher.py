from __future__ import annotations
from typing import Any, Dict
import os
import httpx


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        # Use TAVILY_API_KEY auth token for API call to Vingroup's API
        api_key: str = os.getenv("TAVILY_API_KEY", "")

        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable is not set")

        with httpx.Client(timeout=15) as client:
            # Make GET request to Vingroup's API with TAVILY_API_KEY auth token
            resp = client.get(
                "https://api.example.com/vinfast/revenue/2024",  # Replace with actual API endpoint
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()

        data: dict = resp.json()
        return {
            "status": "success",
            "revenue_data": data,  # Output key as per coder notes
            "summary": "Fetched revenue data from Vingroup's API successfully",
        }
    except httpx.HTTPStatusError as exc:
        return {"status": "error", "data": {}, "summary": f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"}
    except Exception as exc:
        return {"status": "error", "data": {}, "summary": str(exc)}
