from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Retrieves a random image from a data source and extracts its short description.

    Args:
        input_data (Optional[Dict[str, Any]], optional): Input data for the skill.
            Expected keys are `url`, `headers`, `payload`.
        timeout (int, optional): Timeout in seconds. Defaults to 30.

    Returns:
        Dict[str, Any]: Output of the skill with keys "status", "data" and "summary".
    """
    
    input_data = input_data or {}
    try:
        url: str     = input_data.get("url", os.getenv("TARGET_URL", ""))
        headers: dict = input_data.get("headers", {})
        payload: dict = input_data.get("payload", {})

        if not url:
            raise ValueError("'url' is required in input_data or TARGET_URL env var")

        with httpx.Client(timeout=30) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()

        data: dict      = resp.json()
        image_url: str  = data.get("image_url", "")
        short_description: str = data.get("short_description", "")

        return {
            "status": "success",
            "data": {"image_url": image_url, "short_description": short_description},
            "summary": f"Found an image at {url}",
        }
    except httpx.HTTPStatusError as exc:
        return {"status": "error", "data": {}, "summary": f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"}
    except Exception as exc:
        return {"status": "error", "data": {}, "summary": str(exc)}
