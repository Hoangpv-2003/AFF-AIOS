import httpx
from typing import Dict, Any, Optional
import os

def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return {
                "status": "error",
                "summary": "Không tìm thấy API key cho Tavily.",
                "error_reason": "Thiếu biến môi trường TAVILY_API_KEY."
            }
        url = "https://api.tavily.com/search"
        params = {"topic": input_data.get("topic", "")}
        headers = {"Authorization": f"Bearer {api_key}"}
        response = httpx.post(url, params=params, headers=headers)
        response.raise_for_status()
        report_url = response.json().get("url")
        if not report_url:
            return {"status": "error", "summary": "Không tìm thấy báo cáo.", "error_reason": "Không có URL trong kết quả tìm kiếm."}
        return {
            "status": "success",
            "summary": f"Báo cáo đã được tạo: {report_url}",
            "report": report_url
        }
    except Exception as e:
        return {
            "status": "error",
            "summary": "Lỗi khi tạo báo cáo.",
            "error_reason": str(e)
        }