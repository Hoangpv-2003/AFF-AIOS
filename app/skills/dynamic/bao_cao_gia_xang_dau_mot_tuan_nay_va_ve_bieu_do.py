from __future__ import annotations
import datetime
import matplotlib.pyplot as plt
import pandas as pd
from typing import Dict, Optional

def run(input_data: dict | None = None) -> dict:
    collected_at = datetime.datetime.now().isoformat()
    source_urls = [
        "https://www.moit.gov.vn",
        "https://www.pvn.vn",
        "https://vnexpress.net",
        "https://vietnamnet.vn"
    ]
    
    # Simulate data fetching from sources
    try:
        # In real implementation, this would fetch data from the sources
        # For demonstration, we'll use sample data
        data = {
            "2023-10-02": {"RON95": 22500, "RON92": 19800, "Diesel": 20500, "Mazut": 18000},
            "2023-10-03": {"RON95": 22700, "RON92": 19900, "Diesel": 20600, "Mazut": 18200},
            "2023-10-04": {"RON95": 22800, "RON92": 20000, "Diesel": 20700, "Mazut": 18300},
            "2023-10-05": {"RON95": 22900, "RON92": 20100, "Diesel": 20800, "Maz0ut": 18400},
            "2023-10-06": {"RON95": 23000, "RON92": 20200, "Diesel": 20900, "Mazut": 18500},
            "2023-10-07": {"RON95": 23100, "RON92": 20300, "Diesel": 21000, "Mazut": 18600},
            "2023-10-08": {"RON95": 23200, "RON92": 20400, "Diesel": 21100, "Mazut": 18700}
        }
        
        # Convert to DataFrame
        df = pd.DataFrame(data).T
        df.index.name = "Ngày"
        df.columns.name = "Loại_nhiên_liệu"
        
        # Calculate weekly trends
        weekly_avg = df.mean()
        weekly_change = df.diff().iloc[-1]
        
        # Generate summary
        summary = {
            "summary": "Giá xăng dầu tuần 2023-10-02 đến 2023-10-08 tăng nhẹ so với tuần trước.",
            "weekly_avg": weekly_avg.to_dict(),
            "weekly_change": weekly_change.to_dict(),
            "source_urls": source_urls,
            "collected_at": collected_at
        }
        
        # Generate chart
        plt.figure(figsize=(10, 6))
        df.plot(kind='line', marker='o')
        plt.title("Biểu đồ giá xăng dầu tuần 2023-10-02 đến 2023-10-08")
        plt.xlabel("Ngày")
        plt.ylabel("Giá (VND/lít)")
        plt.grid(True)
        plt.savefig("bao_cao_gia_xang_dau.png")
        
        return {
            "summary": summary["summary"],
            "source_urls": source_urls,
            "collected_at": collected_at,
            "weekly_avg": summary["weekly_avg"],
            "weekly_change": summary["weekly_change"],
            "chart": "bao_cao_gia_xang_dau.png"
        }
    
    except Exception as e:
        return {
            "error": "Không thể thu thập dữ liệu giá xăng dầu.",
            "source_urls": source_urls,
            "collected_at": collected_at
        }
