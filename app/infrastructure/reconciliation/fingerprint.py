"""Deterministic fingerprint helpers for reconciliation."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


def _normalize_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {key: _normalize_payload(payload[key]) for key in sorted(payload.keys())}
    if isinstance(payload, list):
        return [_normalize_payload(item) for item in payload]
    return payload


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compute_skill_digest(payload: Mapping[str, Any]) -> str:
    normalized = _normalize_payload(dict(payload))
    packed = json.dumps(normalized, separators=(",", ":"), sort_keys=True)
    return _sha256_hex(packed)


def git_fingerprint(commit_sha: str, tree_sha: str, path: str) -> str:
    packed = "|".join([commit_sha.strip(), tree_sha.strip(), path.strip().replace("\\", "/")])
    return _sha256_hex(packed)


def compute_snapshot_fingerprint(snapshot: Mapping[str, str]) -> str:
    packed = "\n".join(f"{key}:{snapshot[key]}" for key in sorted(snapshot.keys()))
    return _sha256_hex(packed)
