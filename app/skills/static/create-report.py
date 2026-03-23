from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _extract_values(results: List[dict]) -> List[float]:
    values: List[float] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        content = str(item.get("content", ""))
        for token in content.replace(",", " ").split():
            token = token.strip().replace(".", "")
            if token.isdigit() and len(token) >= 3:
                try:
                    values.append(float(token))
                    break
                except Exception:
                    continue
    return values


def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    payload = dict(input_data or {})
    results = payload.get("results", [])
    source_urls = payload.get("source_urls", [])

    if not isinstance(results, list):
        results = []
    if not isinstance(source_urls, list):
        source_urls = []

    if not results:
        return {
            "status": "error",
            "summary": "Không có dữ liệu đầu vào để tạo báo cáo.",
            "error_reason": "missing_results",
            "report": "",
            "chart_data": None,
            "source_urls": source_urls,
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }

    numbers = _extract_values(results)
    total = sum(numbers) if numbers else 0.0
    avg = (total / len(numbers)) if numbers else 0.0

    lines = [
        "# Báo cáo doanh thu VinFast (tháng)",
        f"- Thời gian tạo: {datetime.now(timezone.utc).isoformat()}",
        f"- Số nguồn tham chiếu: {len(source_urls)}",
        f"- Mẫu dữ liệu định lượng trích xuất: {len(numbers)}",
        f"- Tổng giá trị mẫu: {total:,.0f}",
        f"- Trung bình mẫu: {avg:,.0f}",
        "",
        "## Tóm tắt",
        "Đã tổng hợp dữ liệu nguồn và tạo báo cáo dạng văn bản.",
    ]

    chart_data = {
        "labels": [f"Nguồn {idx+1}" for idx in range(min(len(numbers), 12))],
        "series": numbers[:12],
        "unit": "VND (mẫu trích xuất)",
    }

    return {
        "status": "success",
        "summary": "Báo cáo doanh thu đã được tạo.",
        "report": "\n".join(lines),
        "chart_data": chart_data,
        "source_urls": source_urls,
        "results": results,
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }