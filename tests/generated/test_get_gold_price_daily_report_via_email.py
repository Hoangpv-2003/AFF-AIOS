from __future__ import annotations
import pytest
from app.skills.dynamic.get_gold_price_daily_report_via_email import run

def test_run():
    result = run()
    assert isinstance(result, dict)
    assert 'status' in result
    assert result['status'] in ['success', 'error']
