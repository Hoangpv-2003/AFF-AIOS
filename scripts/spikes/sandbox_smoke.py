"""Sandbox offline smoke placeholder.

Expected output: JSON report with startup latency, outbound attempts, and pass rate.
"""

import json


if __name__ == "__main__":
    report = {
        "scenario": "sandbox_offline",
        "startup_p95_ms": None,
        "outbound_attempts": None,
        "pass_rate": None,
        "status": "not_implemented",
    }
    print(json.dumps(report, indent=2))
