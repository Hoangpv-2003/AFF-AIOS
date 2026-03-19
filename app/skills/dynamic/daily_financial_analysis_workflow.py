from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
import httpx
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from bs4 import BeautifulSoup

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        topic: str      = input_data.get("topic", "")
        recipient: str  = input_data.get("recipient", "")

        if not topic:
            raise ValueError("'topic' is required in input_data")
        if not recipient:
            raise ValueError("'recipient' is required in input_data")

        with httpx.Client(timeout=15) as client:
            resp = client.post(
                "https://api.tavily.com/search",
                json={"api_key": os.getenv("TAVILY_API_KEY", ""),
                      "query": topic, "max_results": 5, "include_images": True},
            )
            resp.raise_for_status()

        data: dict            = resp.json()
        image_urls: List[str] = data.get("images", [])
        results: List[dict]   = data.get("results", [])

        # Process API data using pandas
        df = pd.DataFrame(results)
        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        ax.bar(df["category"], df["value"])
        fig.savefig("chart.png")

        # Encode PNG as base64 and return dict with 'image_base64' key.
        with open("chart.png", "rb") as f:
            image_data = f.read().encode("base64")
        image_base64 = image_data.decode()

        return {
            "status": "success",
            "summary": f"Found {len(results)} result(s) and {len(image_urls)} image(s) for '{topic}'",
            "data": {"results": results, "image_base64": image_base64},
        }
    except Exception as exc:
        return {"status": "error", "summary": str(exc), "data": {}}
