from __future__ import annotations
from app.skills.dynamic.verify_new_90b280 import run

def test_run_returns_dict_with_status():
    result = run()
    assert isinstance(result, dict)
    assert "status" in result
