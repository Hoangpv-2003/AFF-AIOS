def run(input_data=None, **kwargs):
    input_data = input_data or {}
    if "results" not in input_data:
        return {
            "status": "error",
            "summary": "Không có dữ liệu kết quả để tạo báo cáo.",
            "error_reason": "Thiếu khóa 'results' trong input_data"
        }
    
    results = input_data["results"]
    report = []
    total_revenue = 0
    
    for result in results:
        if "month" not in result or "revenue" not in result:
            continue
            
        try:
            month = result["month"]
            revenue = float(result["revenue"])
            report.append({
                "month": month,
                "revenue": revenue,
                "currency": "VND"
            })
            total_revenue += revenue
        except (KeyError, ValueError, TypeError) as e:
            return {
                "status": "error",
                "summary": f"Không thể xử lý dữ liệu kết quả: {str(e)}",
                "error_reason": "Dữ liệu không hợp lệ trong 'results'"
            }
    
    if not report:
        return {
            "status": "error",
            "summary": "Không tìm thấy dữ liệu doanh thu hợp lệ.",
            "error_reason": "Tất cả kết quả đều không chứa thông tin doanh thu"
        }
    
    return {
        "status": "success",
        "summary": f"Báo cáo doanh thu hàng tháng đã được tạo. Tổng doanh thu: {total_revenue} VND",
        "report": report
    }