from __future__ import annotations
from typing import Any, Dict, List
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    
    try:
        results: List[dict] = input_data.get("results", [])
        image_urls: List[str] = input_data.get("image_urls", [])

        if not results or not image_urls:
            return {"status": "success", "summary": ""}

        # Process search results into a Pandas DataFrame
        data = []
        for res in results:
            content = res["content"].lower()
            price_match = re.search(r"(\d+\.\d+)", content)
            if price_match:
                price = float(price_match.group(0))
                data.append({"price": price, "source": content})

        df = pd.DataFrame(data)

        # Generate a simple line chart with Matplotlib
        plt.figure(figsize=(8, 6))
        plt.plot(df["price"], label="Price (VND)")
        plt.xlabel("Source")
        plt.ylabel("Price")
        plt.title("Fuel Prices in February 2026")
        plt.legend()

        # Plot the chart using Plotly Express
        fig = px.line(df, x=df.index, y="price", title="Fuel Prices in February 2026")

        # Return dict with 'summary' and 'data' keys
        summary = f"Found {len(results)} sources of fuel price data."
        return {
            "status": "success",
            "summary": summary[:400],
            "data": {
                "chart_png": plt_to_base64(plt),
                "plotly_json": fig.to_plotly_json(),
            },
        }
    except Exception as exc:
        return {"status": "error", "summary": str(exc)}


def plt_to_base64(fig: plt.Figure) -> bytes:
    import base64
    buf = bytes()
    fig.savefig(buf, format="png")
    plt.close(fig)
    img_b64 = base64.b64encode(buf).decode("utf-8")
    return img_b64.encode("utf-8")
