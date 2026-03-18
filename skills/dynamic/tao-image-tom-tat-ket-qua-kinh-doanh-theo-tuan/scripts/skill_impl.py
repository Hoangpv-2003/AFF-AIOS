from __future__ import annotations
from datetime import datetime
import json

def run(input_data: dict | None = None) -> dict:
    try:
        # Default data if input_data is None
        if input_data is None:
            input_data = {
                "sales_data": [
                    {"week": "Week 1", "revenue": 150000, "units": 250},
                    {"week": "Week 2", "revenue": 180000, "units": 300},
                    {"week": "Week 3", "revenue": 165000, "units": 275},
                    {"week": "Week 4", "revenue": 210000, "units": 350}
                ],
                "target": 200000
            }
        
        # Process data
        total_revenue = sum(item["revenue"] for item in input_data["sales_data"])
        total_units = sum(item["units"] for item in input_data["sales_data"])
        avg_weekly_revenue = total_revenue / len(input_data["sales_data"])
        performance_percentage = (total_revenue / input_data["target"]) * 100 if input_data["target"] else 0
        
        # Generate summary
        report_summary = {
            "total_revenue": total_revenue,
            "total_units": total_units,
            "average_weekly_revenue": avg_weekly_revenue,
            "performance_percentage": round(performance_percentage, 2),
            "trend": "Increasing" if avg_weekly_revenue > input_data["target"] else "Below Target"
        }
        
        # Simulate image generation (mock URL)
        image_url = "https://example.com/weekly-report.png"
        
        return {
            "status": "success",
            "message": "Image created successfully",
            "image_url": image_url,
            "report_summary": report_summary,
            "confidence": 0.85,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "image_url": "",
            "report_summary": {},
            "confidence": 0.0,
            "timestamp": datetime.now().isoformat()
        }
