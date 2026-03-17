"""Sandbox execution request and result models."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SandboxRequest(BaseModel):
    skill_id: str
    command: str
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    working_dir: Optional[str] = None
    requires_network: bool = False
    timeout_seconds: int = 30
    cpu_millis_limit: int = 1000
    memory_mb_limit: int = 256


class SandboxResult(BaseModel):
    success: bool
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    outbound_attempted: bool = False
    outbound_blocked: bool = False
    policy_violations: List[str] = Field(default_factory=list)
    artifacts: List[str] = Field(default_factory=list)
    duration_ms: int = 0
