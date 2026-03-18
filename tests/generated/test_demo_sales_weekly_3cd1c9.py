from __future__ import annotations

import pytest
from app.skills.dynamic.demo_sales_weekly_3cd1c9 import run

def test_run_returns_dict_with_status():
    result = run()
    assert isinstance(result, dict)
    assert 'status' in result.keys()
