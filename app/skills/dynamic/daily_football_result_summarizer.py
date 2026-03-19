from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
import httpx
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        topic: str          = input_data.get("topic", "")
        data_source: str    = input_data.get("data_source", "")

        if not topic:
            raise ValueError("'topic' is required in input_data")
        if not data_source:
            raise ValueError("'data_source' is required in input_data")

        with httpx.Client(timeout=15) as client:
            # Use Tavily API to fetch latest football results
            resp = client.post(
                "https://api.tavily.com/search",
                json={"api_key": os.getenv("TAVILY_API_KEY", ""),
                      "query": topic,
                      "max_results": 5, "include_images": False},
            )
            resp.raise_for_status()

        data: dict            = resp.json()
        results: List[dict]   = data.get("results", [])

        # Process data and generate summary
        df = pd.DataFrame(results)
        summary = ""
        for index, row in df.iterrows():
            summary += f"{row['team']} vs {row['opponent']}: {row['result']} | "
        summary = summary[:-3]

        # Generate image of chart
        fig = px.bar(df, x='team', y='result')
        fig.update_layout(title=f"Daily Football Results Summary",
                          xaxis_title="Team",
                          yaxis_title="Result")
        plt.savefig("image.png", bbox_inches='tight')

        # Encode PNG as base64
        with open('image.png', 'rb') as f:
            image_base64 = f.read().decode()

        return {
            "status": "success",
            "summary": summary,
            "image_base64": image_base64,
            "summary": f"Generated daily football results summary and image for {topic}",
        }
    except Exception as exc:
        return {"status": "error", "summary": "", "image_base64": "", "summary": str(exc)}
