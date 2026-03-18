from __future__ import annotations
import pytest
from app.skills.dynamic.tao_skill_chuan_hoa_email_va_kiem_tra_dinh_dang import run

def test_run():
    result = run()
    assert isinstance(result, dict)
    assert 'status' in result
