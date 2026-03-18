from __future__ import annotations
from typing import Dict, Optional

def run(input_data: Dict | None = None) -> Dict:
    if input_data is None:
        current_price = {
            "usd": "$4350-$4550",
            "vnd": "89-91 triệu VND"
        }
        trend = "Tăng mạnh, đạt đỉnh mới"
        volatility = "Cao, có sự biến động mạnh"
        historical_high = "89-91 triệu VND (2025)"
        image_summary = "Biểu đồ giá vàng thế giới (XAU/USD) với xu hướng tăng và biến động"
        source_links = [
            "https://www.scribd.com/document/981751266/Gia-Vang",
            "https://vn.tradingview.com/symbols/XAUUSD/",
            "https://www.tierra.vn/tin-tuc/bieu-do-gia-vang-the-gioi-xau-usd"
        ]
    else:
        current_price = input_data.get("current_price", {})
        trend = input_data.get("trend", "Tăng mạnh")
        volatility = input_data.get("volatility", "Cao")
        historical_high = input_data.get("historical_high", "89-91 triệu VND")
        image_summary = input_data.get("image_summary", "Biểu đồ giá vàng thế giới")
        source_links = input_data.get("source_links", [])
    
    return {
        "current_price": current_price,
        "trend": trend,
        "volatility": volatility,
        "historical_high": historical_high,
        "image_summary": image_summary,
        "source_links": source_links
    }
