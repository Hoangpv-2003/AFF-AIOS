from __future__ import annotations

from app.skills.dynamic.tao_report_gia_vang_va_tao_hinh_anh_tom_tat import run

def test_run_returns_dict_with_status():
    result = run()
    assert isinstance(result, dict)
    assert 'status' in result
