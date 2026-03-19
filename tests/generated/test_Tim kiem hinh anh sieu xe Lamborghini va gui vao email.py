from __future__ import annotations

from app.skills.dynamic.Tim_kiem_hinh_anh_sieu_xe_Lamborghini_va_gui_vao_email import run

def test_run_returns_dict_with_status():
    result = run()
    assert isinstance(result, dict)
    assert 'status' in result
    assert result['status'] in ['success', 'error']
