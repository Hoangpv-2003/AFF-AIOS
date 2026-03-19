from __future__ import annotations
from app.skills.dynamic import run
import pytest

def test_run_returns_dict_with_status():
    result = run()
    assert isinstance(result, dict)
    assert 'status' in result

def test_run_status_is_success_or_error():
    result = run()
    status = result['status']
    assert status in ['success', 'error']
