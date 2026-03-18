from __future__ import annotations

import base64
import io
from datetime import datetime
from typing import Dict, List, Tuple


def _sample_data() -> Tuple[List[str], List[float]]:
    # Sample data is used only when input_data is None.
    return (
        ["2026-01-05", "2026-01-20", "2026-02-05", "2026-02-20", "2026-03-05"],
        [81.2, 82.5, 84.1, 83.0, 85.4],
    )


def _validate_input(input_data: Dict) -> Tuple[List[str], List[float]]:
    if not isinstance(input_data, dict):
        raise ValueError("input_data phai la dict hoac None")
    if "dates" not in input_data:
        raise ValueError("Input phai co key 'dates'")
    if "prices" not in input_data:
        raise ValueError("Input phai co key 'prices'")

    dates = input_data.get("dates")
    prices = input_data.get("prices")
    if not isinstance(dates, list):
        raise ValueError("'dates' phai la list string dinh dang YYYY-MM-DD")
    if not isinstance(prices, list):
        raise ValueError("'prices' phai la list so")
    if len(dates) != len(prices):
        raise ValueError("dates va prices phai co cung do dai")
    if len(dates) == 0:
        raise ValueError("dates va prices khong duoc rong")

    normalized_dates: List[str] = []
    for item in dates:
        if not isinstance(item, str):
            raise ValueError("Moi phan tu trong dates phai la string")
        try:
            dt = datetime.strptime(item, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("dates phai dung dinh dang YYYY-MM-DD") from exc
        normalized_dates.append(dt.strftime("%Y-%m-%d"))

    normalized_prices: List[float] = []
    for value in prices:
        if isinstance(value, bool):
            raise ValueError("prices phai la so, khong chap nhan bool")
        try:
            normalized_prices.append(float(value))
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"prices chua gia tri khong phai so: {value}"
            ) from exc

    return normalized_dates, normalized_prices


def _chart_to_base64(dates: List[str], prices: List[float]) -> str:
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(dates, prices, marker="o", linewidth=2)
    ax.set_title("Xu huong gia vang")
    ax.set_xlabel("Ngay")
    ax.set_ylabel("Gia")
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.autofmt_xdate(rotation=30)

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def run(input_data: Dict | None = None) -> Dict:
    """Phan tich gia vang tu du lieu dau vao va tra ve bieu do base64.

    Args:
        input_data: Dict gom:
            - dates: List[str], dinh dang YYYY-MM-DD
            - prices: List[float]
            Neu None thi dung sample data noi bo va danh dau
            is_sample_data=True.

    Returns:
        Dict bat buoc co cac field:
            - dates, prices
            - mean_price, max_price, min_price
            - price_change_pct
            - chart_base64
            - is_sample_data
            - summary

    Raises:
        ValueError: Neu input_data khong hop le.
    """

    is_sample_data = input_data is None
    if is_sample_data:
        dates, prices = _sample_data()
    else:
        dates, prices = _validate_input(input_data)

    count = len(prices)
    mean_price = sum(prices) / count
    max_price = max(prices)
    min_price = min(prices)

    first_price = prices[0]
    last_price = prices[-1]
    if first_price == 0:
        raise ValueError(
            "Gia dau tien khong duoc bang 0 de tinh phan tram thay doi"
        )
    if count == 1:
        price_change_pct = 0.0
    else:
        price_change_pct = ((last_price - first_price) / first_price) * 100.0

    chart_base64 = _chart_to_base64(dates, prices)
    summary = (
        "Du lieu gom "
        f"{count} moc, gia trung binh {mean_price:.2f}, "
        f"cao nhat {max_price:.2f}, thap nhat {min_price:.2f}, "
        f"bien dong {price_change_pct:.2f}%"
    )

    return {
        "dates": dates,
        "prices": prices,
        "mean_price": round(mean_price, 4),
        "max_price": round(max_price, 4),
        "min_price": round(min_price, 4),
        "price_change_pct": round(price_change_pct, 4),
        "chart_base64": chart_base64,
        "is_sample_data": is_sample_data,
        "summary": summary,
    }
