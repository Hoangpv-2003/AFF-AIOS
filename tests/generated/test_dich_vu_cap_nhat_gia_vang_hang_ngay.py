from __future__ import annotations
import pytest
from app.skills.dynamic.dich_vu_cap_nhat_gia_vang_hang_ngay import run

def test_run():
    result = run()
    assert isinstance(result, dict)
    assert 'status' in result
    assert result['status'] in ['success', 'error']
