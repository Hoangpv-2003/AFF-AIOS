from __future__ import annotations

import base64
from pathlib import Path
import importlib.util

import pytest


_MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "skill_impl.py"
)
_SPEC = importlib.util.spec_from_file_location("gold_skill_impl", _MODULE_PATH)
_MODULE = importlib.util.module_from_spec(_SPEC)
assert _SPEC is not None and _SPEC.loader is not None
_SPEC.loader.exec_module(_MODULE)
run = _MODULE.run


def _valid_input() -> dict:
    return {
        "dates": ["2026-01-01", "2026-01-15", "2026-02-01"],
        "prices": [80.0, 82.0, 84.0],
    }


def _assert_required_fields(payload: dict) -> None:
    required = [
        "dates",
        "prices",
        "mean_price",
        "max_price",
        "min_price",
        "price_change_pct",
        "chart_base64",
        "is_sample_data",
        "summary",
    ]
    for field in required:
        assert field in payload, f"Thieu field bat buoc: {field}"


# Happy path voi input that.
def test_happy_path_real_input_returns_valid_schema():
    result = run(_valid_input())
    _assert_required_fields(result)
    assert (
        result["is_sample_data"] is False
    ), "Input that phai co is_sample_data=False"


# Happy path voi input None dung sample data.
def test_happy_path_none_input_uses_sample_data():
    result = run(None)
    _assert_required_fields(result)
    assert (
        result["is_sample_data"] is True
    ), "Input None phai co is_sample_data=True"


# Loi thieu key dates.
def test_missing_dates_key_raises_value_error():
    with pytest.raises(ValueError, match="dates"):
        run({"prices": [1.0, 2.0]})


# Loi thieu key prices.
def test_missing_prices_key_raises_value_error():
    with pytest.raises(ValueError, match="prices"):
        run({"dates": ["2026-01-01", "2026-01-02"]})


# Loi do dai dates va prices khong khop.
def test_mismatched_lengths_raises_value_error():
    with pytest.raises(ValueError, match="cung do dai"):
        run({"dates": ["2026-01-01"], "prices": [1.0, 2.0]})


# Loi prices chua gia tri khong phai so.
def test_non_numeric_prices_raises_value_error():
    with pytest.raises(ValueError, match="khong phai so"):
        run({"dates": ["2026-01-01"], "prices": ["abc"]})


# Loi dinh dang ngay khong dung YYYY-MM-DD.
def test_invalid_date_format_raises_value_error():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        run({"dates": ["01/01/2026"], "prices": [80.0]})


# Output khong duoc chua file path.
def test_output_has_no_disk_path_strings():
    result = run(_valid_input())
    text_blob = str(result)
    assert "\\" not in text_blob, "Output khong duoc chua duong dan file"
    assert ".png" not in text_blob.lower(), "Khong duoc lo ten file anh"
    assert ":\\" not in text_blob, "Khong duoc lo path tuyet doi"


# chart_base64 phai la base64 hop le.
def test_chart_base64_is_valid_base64():
    result = run(_valid_input())
    decoded = base64.b64decode(result["chart_base64"], validate=True)
    assert len(decoded) > 0, "chart_base64 phai decode duoc du lieu"


# is_sample_data phai true khi input None.
def test_is_sample_data_true_when_input_none():
    result = run(None)
    assert result["is_sample_data"] is True, "Input None phai la sample data"


# is_sample_data phai false khi input that.
def test_is_sample_data_false_when_real_input():
    result = run(_valid_input())
    assert (
        result["is_sample_data"] is False
    ), "Input that khong duoc danh dau sample"


# Edge case chi co 1 ngay du lieu.
def test_single_day_data_returns_zero_change_pct():
    result = run({"dates": ["2026-01-01"], "prices": [80.0]})
    assert (
        result["price_change_pct"] == 0.0
    ), "1 diem du lieu thi bien dong phai bang 0"


# Edge case gia bang nhau thi bien dong bang 0.
def test_flat_prices_returns_zero_change_pct():
    result = run(
        {
            "dates": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "prices": [80.0, 80.0, 80.0],
        }
    )
    assert (
        result["price_change_pct"] == 0.0
    ), "Gia khong doi thi bien dong phai bang 0"
