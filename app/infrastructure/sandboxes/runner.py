"""Local sandbox runner used by reviewer pipeline in offline mode."""

from __future__ import annotations

import time

from app.infrastructure.sandboxes.models import SandboxRequest, SandboxResult
from app.infrastructure.sandboxes.policy import SandboxPolicy, SandboxPolicyEvaluator


import subprocess
import threading
import os

try:
    import psutil
except ImportError:
    psutil = None

class LocalSandboxRunner:
    def __init__(self, policy: SandboxPolicy | None = None) -> None:
        self.policy = policy or SandboxPolicy(allow_network=False)
        self._evaluator = SandboxPolicyEvaluator(self.policy)

    def run(self, request: SandboxRequest) -> SandboxResult:
        started = time.perf_counter()
        violations = self._evaluator.evaluate(request)
        outbound_attempted = request.requires_network
        outbound_blocked = "NETWORK_EGRESS_DENIED" in violations

        if violations:
            return SandboxResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr=";".join(violations),
                outbound_attempted=outbound_attempted,
                outbound_blocked=outbound_blocked,
                policy_violations=violations,
                artifacts=[],
                duration_ms=int((time.perf_counter() - started) * 1000),
            )

        # Execution Logic
        cmd = [request.command] + request.args
        timeout = request.timeout_seconds or self.policy.max_timeout_seconds
        mem_limit = request.memory_mb_limit or self.policy.max_memory_mb

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="utf-8",
                errors="replace",
                env={**os.environ, "PYTHONPATH": os.getcwd()},
            )

            # Monitor memory if psutil is available
            if psutil:
                def monitor():
                    try:
                        p = psutil.Process(process.pid)
                        while process.poll() is None:
                            if p.memory_info().rss / (1024 * 1024) > mem_limit:
                                process.kill()
                                break
                            time.sleep(0.1)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                monitor_thread = threading.Thread(target=monitor, daemon=True)
                monitor_thread.start()

            stdout, stderr = process.communicate(timeout=timeout)
            exit_code = process.returncode
            success = (exit_code == 0)

        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            exit_code = 124
            success = False
            stderr += "\n[SANDBOX] Timeout limit exceeded."
        except Exception as e:
            stdout, stderr = "", str(e)
            exit_code = 1
            success = False

        duration_ms = int((time.perf_counter() - started) * 1000)

        return SandboxResult(
            success=success,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            outbound_attempted=outbound_attempted,
            outbound_blocked=False,
            policy_violations=[],
            artifacts=[],
            duration_ms=duration_ms,
        )
