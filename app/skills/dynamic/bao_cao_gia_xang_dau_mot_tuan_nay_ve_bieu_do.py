from __future__ import annotations
import datetime
import json
from typing import Dict, Any

def run(input_data: dict | None = None) -> dict:
    collected_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source_urls = [
        "https://www.moit.gov.vn",
        "https://www.pvpetrol.com.vn",
        "https://www.shell.com.vn",
        "https://www.bp.com.vn"
    ]
    
    # Simulate data collection from sources
    if input_data is None:
        data = []
        try:
            # Simulate fetching data from sources
            for url in source_urls:
                # Simulate API call or web scraping
                # In real scenario, this would fetch actual data
                # Here, we use placeholder data for demonstration
                data.append({
                    "date": "2023-10-01",
                    "fuel_type": "Xăng 95",
                    "price": 25000
                })
                data.append({
                    "date": "2023-10-02",
                    "fuel_type": "Xăng 92",
                    "price": 24500
                })
                data.append({
                    "date": "2023-10-03",
                    "fuel_type": "Dầu Diesel",
                    "price": 20000
                })
                data.append({
                    "date": "2023-10-04",
                    "fuel_type": "Xăng E5",
                    "price": 24000
                })
                data.append({
                    "date": "2023-10-05",
                    "fuel_type": "Xăng 95",
                    "price": 25200
                })
                data.append({
                    "date": "2023-10-06",
                    "fuel_type": "Xăng 92",
                    "price": 24600
                })
                data.append({
                    "date": "2023-10-07",
                    "fuel_type": "Dầu Diesel",
                    "price": 20100
                })
        except Exception as e:
            data = []
    
    # Process data for the past week
    processed_data = []
    if data:
        # Filter data for the past week (simulated)
        for item in data:
            if datetime.datetime.strptime(item["date"], "%Y-%m-%d") >= datetime.datetime.now() - datetime.timedelta(days=7):
                processed_data.append(item)
    
    # Generate summary
    summary = "Báo cáo giá xăng dầu tuần từ 2023-10-01 đến 2023-10-07"
    if not processed_data:
        summary += " (Không có dữ liệu từ nguồn chính thống)"
    
    return {
        "summary": summary,
        "source_urls": source_urls,
        "collected_at": collected_at,
        "data": processed_data
    }
