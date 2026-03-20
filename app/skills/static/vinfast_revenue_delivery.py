from __future__ import annotations
from typing import Any, Dict, Optional
import pandas as pd


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        # Read data from previous skill (vinfast_revenue_analyzer)
        data: dict = input_data.get("data", {})

        # Process revenue data using pandas
        df = pd.DataFrame(data["results"])
        summary = (
            f"Doanh thu VinFast năm 2024 đạt {df['revenue'].sum():.2f} tỷ đồng."
        )

        return {
            "status": "success",
            "summary": summary,
        }
    except Exception as exc:
        return {"status": "error", "summary": str(exc)}
