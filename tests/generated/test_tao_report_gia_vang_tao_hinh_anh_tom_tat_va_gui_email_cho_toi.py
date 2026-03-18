from __future__ import annotations
import pytest
from app.skills.dynamic.tao_report_gia_vang_tao_hinh_anh_tom_tat_va_gui_email_cho_toi import run

def test_run_returns_dict_with_status():
    result = run()
    assert isinstance(result, dict)
    assert 'status' in result
