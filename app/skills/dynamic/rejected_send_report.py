from typing import Dict, Any, Optional
import re

def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    input_data = input_data or {}
    results = input_data.get('results')
    topic = input_data.get('topic')
    
    if not results or not topic:
        return {
            'status': 'error',
            'summary': 'Dữ liệu không đủ để tạo báo cáo',
            'error_reason': 'Thiếu kết quả tìm kiếm hoặc chủ đề báo cáo'
        }
    
    revenue_pattern = re.compile(r'\d+\.?\d*\s*(tỷ|triệu|USD)')
    revenue_matches = revenue_pattern.findall(results)
    
    if not revenue_matches:
        return {
            'status': 'error',
            'summary': 'Không tìm thấy dữ liệu doanh thu trong kết quả',
            'error_reason': 'Kết quả không chứa thông tin tài chính'
        }
    
    try:
        revenue_values = [
            float(match.replace('tỷ', '').replace('triệu', '').replace('USD', '').strip())
            for match in revenue_matches
        ]
        total_revenue = sum(revenue_values)
    except ValueError:
        return {
            'status': 'error',
            'summary': 'Không thể chuyển đổi dữ liệu doanh thu sang số',
            'error_reason': 'Dữ liệu chứa ký hiệu không hợp lệ'
        }
    
    return {
        'status': 'success',
        'summary': f'Báo cáo doanh thu VinFast 2025: {total_revenue} tỷ VND',
        'data': {
            'total_revenue': total_revenue,
            'currency': 'VND',
            'source': topic
        }
    }