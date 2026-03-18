from __future__ import annotations
import pytest
from app.skills.dynamic.tao_skill_thong_ke_doanh_thu_ban_hang_theo_tuan_va_xuat_bao_cao_ import run

def test_run_returns_dict_with_status():
    result = run()
    assert isinstance(result, dict)
    assert 'status' in result
