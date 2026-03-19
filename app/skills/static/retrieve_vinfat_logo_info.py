from __future__ import annotations
from typing import Any, Dict, Optional
import httpx


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        data_source: str = os.getenv("DATA_SOURCE", "")
        if not data_source:
            raise ValueError("'data_source' is required in environment variables")

        url: str = f"{data_source}/vinfast_logo_info"
        with httpx.Client(timeout=10) as client:
            resp = client.get(url)
            resp.raise_for_status()

        data: dict = resp.json()
        vinfast_logo_info: dict = data["vinfast_logo_info"]
        return {
            "status": "success",
            "vinfast_logo_info": vinfast_logo_info,
            "summary": f"Retrieved VinFast logo info from {url}",
        }
    except Exception as exc:
        return {"status": "error", "vinfast_logo_info": {}, "summary": str(exc)}
