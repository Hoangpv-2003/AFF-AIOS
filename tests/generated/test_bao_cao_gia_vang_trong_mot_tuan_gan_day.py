from __future__ import annotations

from app.skills.dynamic.bao_cao_gia_vang_trong_mot_tuan_gan_day import run

def test_run():
    result = run()
    assert isinstance(result, dict)
    assert 'status' in result
