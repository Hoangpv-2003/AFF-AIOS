from __future__ import annotations
from typing import Any, Dict, Optional
import httpx


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        # TAVILY_API_KEY environment variable must be set
        api_key: str = os.getenv("TAVILY_API_KEY", "")
        
        if not api_key:
            raise ValueError("'TAVILY_API_KEY' is required in the environment variables")

        with httpx.Client(timeout=15) as client:
            resp = client.post(
                "https://api.tavily.com/search",
                json={"api_key": api_key, "query": "",
                      "max_results": 3, "include_images": False},
            )
            resp.raise_for_status()

        data: dict = resp.json()
        current_gold_price: float = data.get("gold_price", 0.0)
        
        # Process yesterday and day_before_yesterday
        yesterday_result: Any = input_data.get("yesterday")
        if yesterday_result:
            yesterday_gold_price: float = yesterday_result["gold_price"]
        else:
            yesterday_gold_price: float = data.get("previous_day_gold_price", 0.0)

        day_before_yesterday_result: Any = input_data.get("day_before_yesterday")
        if day_before_yesterday_result:
            day_before_yesterday_gold_price: float = day_before_yesterday_result["gold_price"]
        else:
            day_before_yesterday_gold_price: float = data.get("previous_day_previous_day_gold_price", 0.0)

        return {
            "status": "success",
            "output_keys": ["current_gold_price", "yesterday_gold_price", "day_before_yesterday_gold_price"],
            "current_gold_price": current_gold_price,
            "yesterday_gold_price": yesterday_gold_price,
            "day_before_yesterday_gold_price": day_before_yesterday_gold_price,
            "summary": f"Retrieved gold prices for the last 3 days",
        }
    except Exception as exc:
        return {"status": "error", "output_keys": [], "current_gold_price": None, "yesterday_gold_price": None, "day_before_yesterday_gold_price": None, "summary": str(exc)}
