from __future__ import annotations
import os, httpx
from typing import Any, Dict, Optional, List
def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    results = input_data.get("results", [])
    images = [r.get("image") for r in results if r.get("image")]
    return {"status": "success", "images": images}