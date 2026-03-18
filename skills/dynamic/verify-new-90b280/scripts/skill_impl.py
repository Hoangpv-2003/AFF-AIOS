from __future__ import annotations

def run(input_data: dict | None = None) -> dict:
    if input_data is None:
        return {
            "status": "error",
            "message": "No input data provided",
            "data": {},
            "warnings": []
        }
    
    revenue_data = input_data.get("revenue_data")
    if not revenue_data:
        return {
            "status": "error",
            "message": "No revenue data found",
            "data": {},
            "warnings": []
        }
    
    try:
        sorted_data = sorted(revenue_data, key=lambda x: x["week"])
    except KeyError:
        return {
            "status": "error",
            "message": "Invalid revenue data format",
            "data": {},
            "warnings": []
        }
    
    total_revenue = sum(item["revenue"] for item in sorted_data)
    warnings = []
    
    for i in range(1, len(sorted_data)):
        prev = sorted_data[i-1]
        current = sorted_data[i]
        try:
            change = ((current["revenue"] - prev["revenue"]) / prev["revenue"]) * 100
        except ZeroDivisionError:
            change = float('inf')
        if prev["revenue"] > 0 and change < -20:
            warnings.append({
                "week": current["week"],
                "previous_week": prev["week"],
                "revenue": current["revenue"],
                "previous_revenue": prev["revenue"],
                "percentage_drop": round(change, 2)
            })
    
    return {
        "status": "success",
        "message": "Revenue data processed",
        "data": {
            "total_revenue": total_revenue,
            "weekly_data": sorted_data
        },
        "warnings": warnings
    }
