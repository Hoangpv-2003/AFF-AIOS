Dưới đây là mã Python cho file pytest của module Gửi giá vàng hàng ngày vào email:

```python
from __future__ import annotations
from app.skills.dynamic.giavang_hangngay import run as send_gold_price_daily

def test_run():
    result = send_gold_price_daily()
    assert isinstance(result, dict)
    assert 'status' in result
    assert result['status'] in ['success', 'error']
```
