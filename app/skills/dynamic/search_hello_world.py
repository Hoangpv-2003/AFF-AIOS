from typing import Dict, Optional
import os
import requests
from datetime import datetime

RUNTIME_CONTEXT = {
  "current_datetime": "2026-03-20T11:23:44.520526+07:00",
  "current_date_human": "Friday, 20/03/2026",
  "timezone": "Asia/Ho_Chi_Minh",
  "language": "vi"
}

def run(input_data: Dict = None, **kwargs: Dict) -> Dict:
    """
    Search for 'Hello World' in news articles using Tavily API
    """
    
    # Check if required context is available
    if not RUNTIME_CONTEXT or not RUNTIME_CONTEXT.get("current_datetime"):
        return {
            "error": "Tôi cần biết ngày giờ hiện tại để trả lời chính xác. Vui lòng inject RUNTIME_CONTEXT trước khi tiếp tục."
        }

    # Validate input data
    if input_data is None:
        input_data = {}

    # Check if query contains temporal keywords
    query = input_data.get("query", "Hello World")
    if any(keyword in query.lower() for keyword in ["hôm nay", "hiện tại", "ngày nay"]):
        if not RUNTIME_CONTEXT.get("current_datetime"):
            return {
                "error": "Tôi cần biết ngày giờ hiện tại để trả lời chính xác. Vui lòng inject RUNTIME_CONTEXT trước khi tiếp tục."
            }

    # Tavily API configuration
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    if not TAVILY_API_KEY:
        return {"error": "Tavily API key not found in environment variables"}

    # Make API request
    try:
        response = requests.get(
            "https://api.tavily.com/v1/search",
            params={
                "query": query,
                "api_key": TAVILY_API_KEY,
                "language": RUNTIME_CONTEXT.get("language", "vi")
            }
        )
        response.raise_for_status()
        
        # Extract text snippets
        results = response.json().get("results", [])
        text_snippets = [
            {
                "title": result.get("title"),
                "content": result.get("content"),
                "url": result.get("url"),
                "timestamp": result.get("timestamp")
            }
            for result in results[:5]  # Limit to 5 results
        ]
        
        return {
            "text_snippets": text_snippets,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": f"API request failed: {str(e)}"}