from __future__ import annotations

from app.skills.dynamic.tao_image_tom_tat_ket_qua_kinh_doanh_theo_tuan import run

def test_run_returns_dict_with_status():
    result = run()
    assert isinstance(result, dict)
    assert 'status' in result
