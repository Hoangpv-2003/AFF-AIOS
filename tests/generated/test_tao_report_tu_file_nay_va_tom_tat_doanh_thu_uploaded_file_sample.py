from __future__ import annotations

from app.skills.dynamic.tao_report_tu_file_nay_va_tom_tat_doanh_thu_uploaded_file_sample import run

def test_run_returns_dict_with_status():
    result = run()
    assert isinstance(result, dict)
    assert 'status' in result
