from __future__ import annotations
from typing import Any, Dict, Optional
import httpx


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    
    try:
        query: str = input_data.get("query", "")
        
        if not query:
            raise ValueError("'query' is required in input_data")
        
        api_key: str = os.getenv("TAVILY_API_KEY", "")
        
        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable is not set")
        
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                "https://api.tavily.com/search",
                json={"api_key": api_key, "query": query,
                      "max_results": 5, "include_images": True},
            )
            resp.raise_for_status()
        
        data: dict = resp.json()
        title: str = data.get("title", "")
        description: str = data.get("description", "")
        
        return {
            "status": "success",
            "title": title,
            "description": description,
            "summary": f"Found information about VinFast for query '{query}'"
        }
    except Exception as exc:
        return {"status": "error", "title": "", "description": "", "summary": str(exc)}
