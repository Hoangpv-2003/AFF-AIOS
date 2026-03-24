import os
import json
import urllib.request
from urllib.error import URLError, HTTPError
from typing import Optional, Dict

def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    input_data = input_data or {}
    
    # Check for required RUNTIME_CONTEXT
    if not hasattr(run, "RUNTIME_CONTEXT") or not run.RUNTIME_CONTEXT.get("current_datetime"):
        return {
            "status": "error",
            "summary": "Tôi cần biết ngày giờ hiện tại để trả lời chính xác.",
            "error_reason": "RUNTIME_CONTEXT is missing or current_datetime is empty."
        }
    
    # Validate required input parameter 'topic'
    if 'topic' not in input_data:
        return {
            "status": "error",
            "summary": "Không tìm thấy chủ đề để truy vấn.",
            "error_reason": "Missing 'topic' in input_data."
        }
    
    topic = input_data['topic']
    
    # Retrieve API key from environment variables
    api_key = os.getenv('TAVILY_API_KEY')
    if not api_key:
        return {
            "status": "error",
            "summary": "Không thể truy cập API do thiếu khóa API.",
            "error_reason": "Missing TAVILY_API_KEY environment variable."
        }
    
    # Construct API request
    url = "https://api.tavily.com/search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = json.dumps({"topic": topic}).encode("utf-8")
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req) as response:
            results = json.loads(response.read().decode("utf-8"))
            return {
                "status": "success",
                "summary": "Đã truy vấn dữ liệu từ Tavily.",
                "output": results
            }
    except URLError as e:
        return {
            "status": "error",
            "summary": "Không thể kết nối đến API.",
            "error_reason": str(e.reason)
        }
    except HTTPError as e:
        return {
            "status": "error",
            "summary": f"API trả về mã lỗi {e.code}.",
            "error_reason": str(e.reason)
        }
    except Exception as e:
        return {
            "status": "error",
            "summary": "Đã xảy ra lỗi không xác định.",
            "error_reason": str(e)
        }