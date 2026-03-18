from __future__ import annotations
import requests
from typing import Dict, Optional

def run(input_data: Optional[Dict] = None) -> Dict:
    if input_data is None:
        input_data = {}

    objective = input_data.get('objective')
    if objective != 'tạo skill báo cáo giá vàng 7 ngày gần đây':
        return {
            'error': 'Invalid objective',
            'data': {}
        }

    # Required capabilities
    required_capabilities = ['web_scrapping']

    # Detect required capabilities
    actual_capabilities = []
    for capability in required_capabilities:
        if input_data.get('capabilities', {}).get(capability, False):
            actual_capabilities.append(capability)

    if not actual_capabilities:
        return {
            'error': 'Missing required capabilities',
            'data': {}
        }

    # Fetch real web/API data
    url = 'https://webgia.com/gia-vang/sjc/bieu-do-7-ngay.html'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            html_content = response.text
        else:
            html_content = ''
    except Exception as e:
        return {
            'error': str(e),
            'data': {}
        }

    # Normalize and validate data
    import re
    pattern = r'Giá vàng SJC hôm nay: (\d+) triệu đồng/lượng'
    match = re.search(pattern, html_content)
    if match:
        gold_price = int(match.group(1))
    else:
        return {
            'error': 'Failed to extract data',
            'data': {}
        }

    # Compute metrics and return clear analysis fields
    metrics = {
        'gold_price_7_days': gold_price,
        'trend': 'up' if gold_price > 183000000 else 'down'
    }

    return {
        'success': True,
        'data': metrics
    }
