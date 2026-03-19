from __future__ import annotations
import pytest
from app.skills.dynamic import run

def test_run_returns_dict():
    result = run()
    assert isinstance(result, dict)
    assert 'status' in result

def test_status_is_success_or_error():
    result = run()
    status = result['status']
    assert status in ['success', 'error']
