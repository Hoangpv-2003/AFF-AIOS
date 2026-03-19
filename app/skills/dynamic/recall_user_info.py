from __future__ import annotations
from typing import Any, Dict, Optional
import os
import json


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    
    try:
        name: str  = input_data.get("name", "")  # Use safe defaults if data is missing
        email: str = input_data.get("email", "")

        user_info: dict = {
            "name": name,
            "email": email
        }

        return {
            "status": "success",
            "summary": f"Recalled user's name and email",
            "data": user_info  # This is the output data for the skill
        }
    except Exception as exc:
        return {"status": "error", "summary": str(exc)}
