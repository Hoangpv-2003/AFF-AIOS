"""Sandbox offline smoke runner producing startup and policy metrics."""

import json

from app.infrastructure.sandboxes.models import SandboxRequest
from app.infrastructure.sandboxes.runner import LocalSandboxRunner


def _percentile(values, q):
    ordered = sorted(values)
    idx = int((len(ordered) - 1) * q)
    return ordered[idx]


def run_spike(runs=30):
    runner = LocalSandboxRunner()
    durations = []
    success_count = 0

    for i in range(runs):
        result = runner.run(
            SandboxRequest(
                skill_id=f"safe-{i}",
                command="python",
                args=["skills/dynamic/safe_skill.py"],
                requires_network=False,
            )
        )
        durations.append(result.duration_ms)
        success_count += 1 if result.success else 0

    outbound_result = runner.run(
        SandboxRequest(
            skill_id="net-check",
            command="python",
            args=["skills/dynamic/net_skill.py"],
            requires_network=True,
        )
    )

    return {
        "scenario": "sandbox_offline",
        "runs": runs,
        "startup_p95_ms": _percentile(durations, 0.95),
        "outbound_attempted": outbound_result.outbound_attempted,
        "outbound_blocked": outbound_result.outbound_blocked,
        "pass_rate": round(success_count / float(runs), 4),
        "status": "ok",
    }


if __name__ == "__main__":
    print(json.dumps(run_spike(), indent=2))
