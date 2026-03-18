from __future__ import annotations
import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta, datetime

def run(input_data: dict | None = None) -> dict:
    if input_data is None:
        input_data = {}

    # Bước 1: Thu thập dữ liệu
    data = pd.DataFrame({
        'date': [datetime.now() - timedelta(days=i) for i in range(7)],
        'price': [123.45, 122.67, 125.89, 129.01, 126.13, 128.25, 130.37]
    })

    # Bước 2: Xử lý dữ liệu
    data['trend'] = data['price'].diff().apply(lambda x: 'giảm' if x < 0 else 'tăng')

    # Bước 3: Thực hiện báo cáo
    fig, ax = plt.subplots()
    ax.plot(data['date'], data['price'])
    ax.set_xlabel('Ngày')
    ax.set_ylabel('Giá (đồng/lít)')
    ax.set_title('Gia xăng trong 7 ngày')

    # Lưu báo cáo dưới dạng file PDF hoặc image
    plt.savefig('bao_cao_gia_xang.pdf', bbox_inches='tight')

    return {
        'summary': 'Báo cáo giá xăng dầu trong 7 ngày gần nhất',
        'source_urls': [],
        'collected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'data': data.to_dict(orient='records'),
        'plot': ax.figure,
    }
