from __future__ import annotations
from typing import Any, Dict, List, Optional
import httpx
import json

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    
    try:
        current_gold_price = input_data.get("current_gold_price", 0)
        yesterday_gold_price = input_data.get("yesterday_gold_price", 0)
        day_before_yesterday_gold_price = input_data.get("day_before_yesterday_gold_price", 0)

        # Calculate summary of gold prices
        mean_gold_price = (current_gold_price + yesterday_gold_price + day_before_yesterday_gold_price) / 3
        min_gold_price = min(current_gold_price, yesterday_gold_price, day_before_yesterday_gold_price)
        max_gold_price = max(current_gold_price, yesterday_gold_price, day_before_yesterday_gold_price)

        summary = {
            "mean": mean_gold_price,
            "min": min_gold_price,
            "max": max_gold_price
        }

        return {
            "status": "success",
            "summary": summary
        }
    except Exception as e:
        return {
            "status": "error",
            "summary": str(e)
        }
