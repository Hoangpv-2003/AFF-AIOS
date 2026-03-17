"""Sandbox policy evaluator with deny-by-default controls."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Set

from app.infrastructure.sandboxes.models import SandboxRequest


@dataclass
class SandboxPolicy:
    allow_network: bool = False
    allow_shell_commands: bool = False
    blocked_commands: Set[str] = field(default_factory=lambda: {"powershell", "cmd", "bash", "sh"})
    max_timeout_seconds: int = 60
    max_cpu_millis: int = 2000
    max_memory_mb: int = 512


class SandboxPolicyEvaluator:
    def __init__(self, policy: SandboxPolicy | None = None) -> None:
        self.policy = policy or SandboxPolicy()

    def evaluate(self, request: SandboxRequest) -> list[str]:
        violations: list[str] = []

        if request.requires_network and not self.policy.allow_network:
            violations.append("NETWORK_EGRESS_DENIED")

        if request.command.lower() in self.policy.blocked_commands and not self.policy.allow_shell_commands:
            violations.append("PROCESS_DENIED")

        if request.timeout_seconds > self.policy.max_timeout_seconds:
            violations.append("TIMEOUT_LIMIT_EXCEEDED")

        if request.cpu_millis_limit > self.policy.max_cpu_millis:
            violations.append("CPU_LIMIT_EXCEEDED")

        if request.memory_mb_limit > self.policy.max_memory_mb:
            violations.append("MEMORY_LIMIT_EXCEEDED")

        return violations
