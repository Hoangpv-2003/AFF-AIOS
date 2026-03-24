from typing import Dict, Any, Optional
import httpx
import os
import datetime

def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    input_data = input_data or {}
    runtime_context = input_data.get("runtime_context")
    if not runtime_context:
        return {
            "status": "error",
            "summary": "Missing runtime context",
            "error_reason": "Runtime context is required for date validation"
        }
    current_datetime_str = runtime_context.get("current_datetime")
    if not current_datetime_str:
        return {
            "status": "error",
            "summary": "Missing current datetime",
            "error_reason": "Current datetime is required for date validation"
        }
    try:
        current_datetime = datetime.datetime.fromisoformat(current_datetime_str)
    except ValueError:
        return {
            "status": "error",
            "summary": "Invalid datetime format",
            "error_reason": f"Failed to parse current_datetime: {current_datetime_str}"
        }
    if current_datetime.year != 2025:
        return {
            "status": "error",
            "summary": "Invalid current year",
            "error_reason": "Current year must be 2025 to fetch 2025 data"
        }
    try:
        with httpx.Client() as client:
            response = client.get(
                "https://api.tavily.com/v1/search",
                params={
                    "query": "doanh thu VinFast 2025",
                    "api_key": os.getenv("TAVILY_API_KEY")
                }
            )
            response.raise_for_status()
            data = response.json()
    except httpx.RequestError as e:
        return {
            "status": "error",
            "summary": "Network error",
            "error_reason": f"Failed to fetch data: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "summary": "Unexpected error",
            "error_reason": f"An error occurred: {str(e)}"
        }
    if not data.get("results"):
        return {
            "status": "error",
            "summary": "No results found",
            "error_reason": "No data found for 2025 VinFast revenue"
        }
    extracted_data = []
    sources = []
    for result in data.get("results", []):
        content = result.get("content")
        source = result.get("source")
        if content and source:
            extracted_data.append(content)
            sources.append(source)
    return {
        "status": "success",
        "summary": "Data fetched successfully",
        "data": extracted_data,
        "sources": sources
    }