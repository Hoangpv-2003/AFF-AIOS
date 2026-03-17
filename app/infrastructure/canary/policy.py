"""Canary rollout policy evaluator with quantitative rollback triggers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class CanaryThresholds:
    max_error_rate: float = 0.05
    max_p95_latency_ms: int = 1200
    max_provider_error_rate: float = 0.03
    max_sandbox_denied_rate: float = 0.10


@dataclass
class CanaryDecision:
    action: str
    reason: str
    metrics: Dict[str, float]


class CanaryPolicyEvaluator:
    def __init__(self, thresholds: CanaryThresholds | None = None) -> None:
        self.thresholds = thresholds or CanaryThresholds()

    def evaluate(self, metrics: Dict[str, float]) -> CanaryDecision:
        error_rate = float(metrics.get("error_rate", 0.0))
        p95_latency_ms = float(metrics.get("p95_latency_ms", 0.0))
        provider_error_rate = float(metrics.get("provider_error_rate", 0.0))
        sandbox_denied_rate = float(metrics.get("sandbox_denied_rate", 0.0))

        if error_rate > self.thresholds.max_error_rate:
            return CanaryDecision("rollback", "ERROR_RATE_EXCEEDED", metrics)
        if p95_latency_ms > self.thresholds.max_p95_latency_ms:
            return CanaryDecision("rollback", "LATENCY_P95_EXCEEDED", metrics)
        if provider_error_rate > self.thresholds.max_provider_error_rate:
            return CanaryDecision("rollback", "PROVIDER_ERROR_RATE_EXCEEDED", metrics)
        if sandbox_denied_rate > self.thresholds.max_sandbox_denied_rate:
            return CanaryDecision("rollback", "SANDBOX_DENIED_RATE_EXCEEDED", metrics)

        return CanaryDecision("proceed", "WITHIN_SLO", metrics)
