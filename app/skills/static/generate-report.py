from __future__ import annotations
import os
import httpx
import json
from typing import Any, Dict, Optional

def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    topic = input_data.get("topic")
    results = input_data.get("results")
    summary_text = input_data.get("summary_text")
    
    # Check for RUNTIME_CONTEXT and extract current date
    current_datetime = os.environ.get("RUNTIME_CONTEXT", {}).get("current_datetime")
    if not current_datetime:
        return {"status": "error", "summary": "Không thể xác định thời gian hiện tại."}
    
    report_date = current_datetime.split("T")[0]  # Extract date part
    
    # Define the report template
    template = """
**Báo cáo doanh thu Viettel năm 2025**
Ngày báo cáo: {report_date}

## Tổng quan
{summary_text}

## Kết luận
Báo cáo này tổng hợp các thông tin về doanh thu của Viettel năm 2025 dựa trên dữ liệu tìm kiếm.
"""
    
    # Format the report with dynamic content
    report = template.format(report_date=report_date, summary_text=summary_text)
    
    return {"status": "success", "report": report}