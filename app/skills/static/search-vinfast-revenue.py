from __future__ import annotations
import os, httpx
from typing import Any, Dict, Optional
def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    q = input_data.get("topic") if input_data else "doanh thu VinFast năm 2025"
    key = os.getenv("TAVILY_API_KEY")
    with httpx.Client() as cl:
        r = cl.post("https://api.tavily.com/search", json={
            "api_key": key, "query": q, "include_images": True, "search_depth": "advanced"
        })
        r.raise_for_status()
    data = r.json()
    results = data.get("results", [])
    # Proactive Summary for Email
    summary_text = "Tóm tắt thông tin:\n"
    for r in results[:3]:
        summary_text += f"- {r.get('title')}: {r.get('content')[:150]}...\n"
    return {
        "status": "success", 
        "results": results, 
        "images": data.get("images", []),
        "summary_text": summary_text,
        "summary": "found info"
    }