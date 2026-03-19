from __future__ import annotations
from typing import Any, Dict, Optional
import os
import json
import httpx
import pandas as pd  # Added pandas for data manipulation
import matplotlib.pyplot as plt  # Added matplotlib for chart generation
import plotly.express as px  # Added plotly express

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    
    try:
        vinfast_api_key: str = os.getenv("VINFAST_API_KEY", "")  # Move sensitive credentials to environment variables
        
        if not vinfast_api_key:
            raise ValueError("VINFAST_API_KEY environment variable is not set")

        with httpx.Client(timeout=15) as client:
            resp = client.get(
                "https://api.vinfast.com/financials",
                headers={"Authorization": f"Bearer {vinfast_api_key}"},
            )
            resp.raise_for_status()

        data: dict = resp.json()
        
        # Fetch historical financial data from VinFast API
        vinfast_data: pd.DataFrame = pd.json_normalize(data["data"])
        
        # Perform calculations for revenue 2024
        revenue_2024: float = vinfast_data.loc[vinfast_data['year'] == 2024, 'revenue'].sum()
        
        # Generate chart using matplotlib or plotly express
        fig = px.bar(vinfast_data, x='year', y='revenue')
        plt.show()
        
        return {
            "status": "success",
            "data": {"revenue_2024": revenue_2024},
            "summary": f"VinFast's 2024 revenue: ${revenue_2024:.2f}",
        }
    except Exception as exc:
        return {"status": "error", "data": {}, "summary": str(exc)}
