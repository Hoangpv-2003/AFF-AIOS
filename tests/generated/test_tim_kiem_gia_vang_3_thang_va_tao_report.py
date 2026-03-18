from __future__ import annotations

import pytest
from app.skills.dynamic.tim_kiem_gia_vang_3_thang_va_tao_report import run

def test_run_returns_dict_with_status():
    result = run()
    assert isinstance(result, dict)
    assert 'status' in result
