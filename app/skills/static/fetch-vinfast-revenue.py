from __future__ import annotations
import os, httpx
from typing import Any, Dict, Optional
def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    q = input_data.get("topic")
    key = os.getenv("TAVILY_API_KEY")
    with httpx.Client() as cl:
        r = cl.post("https://api.tavily.com/search", json={"api_key": key, "query": q})
        r.raise_for_status()
    return {"status": "success", "results": r.json().get("results", []), "summary": "found info"}