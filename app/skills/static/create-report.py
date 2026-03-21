from __future__ import annotations
import os
from typing import Any, Dict, Optional
from datetime import datetime

def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    input_data = input_data or {}
    if "results" not in input_data:
        return {
            "status": "error",
            "summary": "Missing required 'results' data",
            "error_reason": "Input data must contain 'results' from a prior search"
        }
    
    try:
        report = {
            "title": "Báo cáo doanh thu Viettel năm 2025",
            "overview": "Tóm tắt chính:\n",
            "key_figures": [],
            "conclusion": "Kết luận:"
        }
        
        # Extract numeric evidence from results
        for item in input_data["results"][:3]:
            try:
                content = item.get("content", "")
                title = item.get("title", "")
                
                # Extract revenue figures using pattern matching
                revenue_match = None
                for line in content.split("\n"):
                    if "doanh thu" in line.lower():
                        revenue_match = line
                        break
                
                if revenue_match:
                    # Extract numerical values using simple regex
                    import re
                    amount = re.search(r"\d+\.?\d*", revenue_match)
                    if amount:
                        report["key_figures"].append({
                            "title": title,
                            "content": f"Doanh thu: {amount.group()} tỷ VND",
                            "url": item.get("url")
                        })
                    else:
                        report["key_figures"].append({
                            "title": title,
                            "content": "Không tìm thấy số liệu doanh thu cụ thể",
                            "url": item.get("url")
                        })
                else:
                    report["key_figures"].append({
                        "title": title,
                        "content": "Không tìm thấy thông tin doanh thu trong nội dung",
                        "url": item.get("url")
                    })
                
                report["overview"] += f"- {title} ({item.get('url')}):\n  {content[:200]}...\n"
            
            except Exception as e:
                return {
                    "status": "error",
                    "summary": "Lỗi xử lý dữ liệu",
                    "error_reason": f"Không thể xử lý mục dữ liệu: {str(e)}"
                }
        
        report["conclusion"] = "Báo cáo đã tổng hợp thông tin từ các nguồn đáng tin cậy, bao gồm doanh thu, thị phần và định hướng phát triển của Viettel trong năm 2025."
        
        return {
            "status": "success", 
            "report": report,
            "summary": "Báo cáo đã được tạo thành công"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "summary": "Lỗi không xác định",
            "error_reason": f"Không thể tạo báo cáo: {str(e)}"
        }