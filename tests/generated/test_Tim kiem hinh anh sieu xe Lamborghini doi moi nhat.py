from __future__ import annotations
import pytest
from app.skills.dynamic.Tim kiem hinh anh sieu xe Lamborghini doi moi nhat import run

def test_run_returns_dict():
    result = run()
    assert isinstance(result, dict)
    assert 'status' in result

def test_run_status_valid():
    result = run()
    status = result['status']
    assert status in ['success', 'error']
