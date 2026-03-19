from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx
import matplotlib.pyplot as plt  # Import plot library


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        analysis_summary: Dict[str, Any] = input_data.get("analysis_summary", {})

        if not analysis_summary:
            raise ValueError("'analysis_summary' must be provided")

        # Generate chart using plot library
        plt.figure(figsize=(8, 6))
        data = analysis_summary.get("data")
        if data is None:
            raise ValueError("Analysis summary 'data' key is missing")
        plt.plot(data["revenue"], label="Revenue")
        plt.xlabel("Time")
        plt.ylabel("Revenue (USD)")
        plt.title("VinFast Revenue Analysis 2024")
        chart = plt.gcf()
        chart.savefig("chart.png", bbox_inches="tight")

        # Encode chart as base64
        with open("chart.png", "rb") as f:
            image_data = f.read()

        # Return encoded image and summary
        return {
            "status": "success",
            "summary": analysis_summary.get("summary", ""),
            "image_base64": "data:image/png;base64," + image_data.decode(),
        }
    except Exception as exc:
        return {"status": "error", "summary": str(exc)}
