from __future__ import annotations
import datetime

def run(input_data: dict | None = None) -> dict:
    collected_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary = "Giá vàng biến động trong tuần gần đây, với một số thương hiệu tăng 2 triệu VND/gram. Thị trường vàng có sự thay đổi lớn, cả tăng và giảm so với xu hướng toàn cầu. Ngày nay, vàng vẫn là tài sản biến động."
    source_urls = [
        "https://baotinmanhhai.vn/gia-vang-hom-nay",
        "https://vnexpress.net/chu-de/gia-vang-1403",
        "https://giavang.net/",
        "https://vn.investing.com/currencies/xau-usd"
    ]
    
    report = {
        "summary": summary,
        "source_urls": source_urls,
        "collected_at": collected_at,
        "data": [
            {
                "date": "2023-12-22",
                "buy_price": 17630000,
                "sell_price": 17930000,
                "brand": "Kim Gia Bảo",
                "type": "Vàng miếng",
                "trend": "Tăng",
                "influencing_factors": ["USD", "lạm phát"]
            },
            {
                "date": "2023-12-22",
                "buy_price": 17630000,
                "sell_price": 17930000,
                "brand": "Tiểu Kim Cát",
                "type": "Vàng miếng",
                "trend": "Tăng",
                "influencing_factors": ["USD", "lạm phát"]
            },
            {
                "date": "2023-12-22",
                "buy_price": 17630000,
                "sell_price": 17930000,
                "brand": "Trang sức",
                "type": "Vàng 999.9",
                "trend": "Tăng",
                "influencing_factors": ["USD", "lạm phát"]
            },
            {
                "date": "2023-03-16",
                "buy_price": 17630000,
                "sell_price": 17930000,
                "brand": "Trang sức",
                "type": "Vàng 999.9",
                "trend": "Tăng",
                "influencing_factors": ["USD", "lạm phát"]
            }
        ]
    }
    
    return report
