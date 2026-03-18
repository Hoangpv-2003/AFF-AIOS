from __future__ import annotations

from app.skills.dynamic import (
    tim_kiem_gia_vang_va_phan_tich_gia_vang_trong_3_thang_gan_day as gold_skill,
)


def test_run_returns_contract_fields():
    result = gold_skill.run()
    assert isinstance(result, dict)
    assert "mean_price" in result
    assert "chart_base64" in result
    assert "is_sample_data" in result
