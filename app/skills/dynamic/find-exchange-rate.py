from typing import Dict, Optional
import httpx
import os
from datetime import datetime

def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        # Validate input
        topic = input_data.get("topic")
        if not topic:
            return {
                "status": "error",
                "summary": "Missing required topic parameter",
                "error_reason": "The 'topic' key is required but not provided."
            }
        
        # Initialize HTTP client
        client = httpx.Client(base_url="https://api.tavily.com", timeout=10.0)
        
        # Make API request
        response = client.post("/search", json={"topic": topic})
        response.raise_for_status()
        
        # Parse and validate response
        results = response.json().get("results")
        if not results or not isinstance(results, list):
            return {
                "status": "error",
                "summary": "Invalid API response format",
                "error_reason": "The Tavily API returned unexpected data structure."
            }
        
        # Extract numeric evidence (example logic - adjust based on actual API structure)
        exchange_rate = None
        for item in results:
            if "USD/VND" in item.get("content", ""):
                try:
                    # Example extraction - adjust based on actual data format
                    rate = float(item["content"].split(" ")[0])
                    exchange_rate = rate
                    break
                except (ValueError, TypeError):
                    continue
        
        if exchange_rate is None:
            return {
                "status": "error",
                "summary": "No valid exchange rate found",
                "error_reason": "Could not extract USD/VND exchange rate from search results."
            }
        
        return {
            "status": "success",
            "summary": f"Found exchange rate: {exchange_rate:.2f} VND/USD",
            "results": results,
            "exchange_rate": exchange_rate
        }
    
    except httpx.RequestError as e:
        return {
            "status": "error",
            "summary": "Network request failed",
            "error_reason": f"HTTP request error: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "summary": "Unexpected error",
            "error_reason": f"An unexpected error occurred: {str(e)}"
        }