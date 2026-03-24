from typing import Dict, Any, Optional
import httpx
import os
import json

def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    input_data = input_data or {}
    
    # Check runtime context
    runtime_context = input_data.get("runtime_context")
    if not runtime_context or not runtime_context.get("current_datetime"):
        return {
            "status": "error",
            "summary": "Tôi cần biết ngày giờ hiện tại để trả lời chính xác. Vui lòng inject RUNTIME_CONTEXT trước khi tiếp tục."
        }
    
    # Extract topic
    topic = input_data.get("topic")
    if not topic:
        return {"status": "error", "summary": "Không tìm thấy chủ đề để truy vấn."}
    
    try:
        client = httpx.Client(base_url="https://api.tavily.com/search", timeout=10.0)
        headers = {"Authorization": f"Bearer {os.getenv("TAVILY_API_KEY")}"}
        response = client.post("", json={"topic": topic}, headers=headers)
        
        if response.status_code != 200:
            return {"status": "error", "summary": f"Lỗi kết nối: {response.status_code}"}
        
        try:
            data = response.json()
            if not data.get("results") or not data.get("source_urls"):
                return {"status": "error", "summary": "Không tìm thấy kết quả phù hợp."}
            
            return {
                "status": "success",
                "summary": f"Đã tìm thấy {len(data["results"]) if data["results"] else 0} kết quả liên quan đến {topic}",
                "results": data.get("results"),
                "source_urls": data.get("source_urls")
            }
        except json.JSONDecodeError:
            return {"status": "error", "summary": "Lỗi giải mã JSON từ API"}
    except httpx.RequestError as e:
        return {"status": "error", "summary": f"Lỗi mạng: {str(e)}"}
    finally:
        if "client" in locals():
            client.close()