from __future__ import annotations

from app.skills.dynamic.tao_skill_phan_tich_chuoi_va_thong_ke_tu import run


def test_generated_word_stats_skill_returns_expected_fields():
    result = run({"text": "a b b c"})
    assert result["total_words"] == 4
    assert result["unique_words"] == 3
    assert result["word_frequency"]["b"] == 2
