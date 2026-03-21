from __future__ import annotations
import os, httpx
from typing import Any, Dict, Optional
def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    results = input_data.get("results", [])
    revenue = None
    for r in results:
        content = r.get("content", "")
        if "doanh thu" in content.lower():
            import re
            match = re.search(r'\b\d+\s*(tỷ|triệu)\b', content)
            if match:
                revenue = f"{match.group(0)} VND"
                break
    if revenue:
        return {
            "status": "success", 
            "parsed_data": {"revenue_2025": revenue}, 
            "summary": f"Đã trích xuất doanh thu năm 2025: {revenue}"
        }
    return {
        "status": "error", 
        "summary": "Không tìm thấy thông tin doanh thu năm 2025"
    }