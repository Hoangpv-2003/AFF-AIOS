from __future__ import annotations
from typing import Any, Dict, Optional
import httpx
import json


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        name: str      = input_data.get("name", "")
        email: str     = input_data.get("email", "")

        user_info: dict = {
            "name": name,
            "email": email
        }

        return {
            "status": "success",
            "user_info": user_info,
            "summary": f"Stored name and email for later retrieval"
        }
    except Exception as exc:
        return {"status": "error", "user_info": {}, "summary": str(exc)}
