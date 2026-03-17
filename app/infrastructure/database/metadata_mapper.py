"""Metadata filter normalization for vector store adapters."""

from __future__ import annotations

from typing import Any, Dict


def _normalize_value(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        if "eq" in value:
            return {"op": "eq", "value": value["eq"]}
        if "contains" in value:
            return {"op": "contains", "value": value["contains"]}
        if "min" in value or "max" in value:
            return {
                "op": "range",
                "min": value.get("min"),
                "max": value.get("max"),
            }
        return {"op": "raw", "value": value}
    if isinstance(value, (list, tuple, set)):
        return {"op": "in", "values": list(value)}
    return {"op": "eq", "value": value}


def normalize_filters(filters: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {key: _normalize_value(value) for key, value in filters.items()}
