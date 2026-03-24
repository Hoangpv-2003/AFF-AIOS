def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    input_data = input_data or {}
    if "results" not in input_data:
        return {
            "status": "error",
            "summary": "Thiếu dữ liệu kết quả từ API Tavily.",
            "error_reason": "Không tìm thấy khóa 'results' trong input_data."
        }
    
    results = input_data["results"]
    if not isinstance(results, list) or len(results) == 0:
        return {
            "status": "error",
            "summary": "Dữ liệu kết quả không hợp lệ.",
            "error_reason": "Danh sách kết quả phải chứa ít nhất một phần tử."
        }
    
    try:
        plan = {
            "objective": "Mục tiêu dự án: " + results[0].get("content", "Chưa có dữ liệu"),
            "overview": "Phác thảo tổng quan: " + results[1].get("content", "Chưa có dữ liệu"),
            "workflow": "Dây chuyền công việc theo Agile: Lập kế hoạch, Triển khai, Kiểm thử, Đánh giá",
            "steps": [
                "Bước 1: Xác định yêu cầu chi tiết",
                "Bước 2: Phân tích và thiết kế hệ thống",
                "Bước 3: Triển khai từng sprint",
                "Bước 4: Kiểm thử và tích hợp",
                "Bước 5: Đánh giá kết quả và điều chỉnh"
            ]
        }
        return {
            "status": "success",
            "summary": "Kế hoạch dự án đã được tạo thành công.",
            "plan": plan
        }
    except Exception as e:
        return {
            "status": "error",
            "summary": "Lỗi khi tạo kế hoạch dự án.",
            "error_reason": str(e)
        }