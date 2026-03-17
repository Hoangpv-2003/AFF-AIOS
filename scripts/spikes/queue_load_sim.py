"""Queue latency spike simulator producing deterministic JSON output."""

import json
import time

from app.agents.manager import ManagerAgent
from app.infrastructure.queue.redis_rq_client import RedisRQQueueClient


def _percentile(values, q):
    ordered = sorted(values)
    idx = int((len(ordered) - 1) * q)
    return ordered[idx]


def run_spike(concurrency=20, batch_backlog=100):
    queue = RedisRQQueueClient()
    queue.set_depth("batch", batch_backlog)

    latencies = []
    for i in range(concurrency):
        start = time.perf_counter()
        queue.submit("interactive", {"task_id": f"spike-i-{i}"})
        latencies.append((time.perf_counter() - start) * 1000)

    manager = ManagerAgent(queue_client=queue)
    accepted, reason = manager.evaluate_admission("interactive")

    return {
        "scenario": "queue_latency",
        "concurrency": concurrency,
        "batch_backlog": batch_backlog,
        "interactive_p50_ms": round(_percentile(latencies, 0.50), 3),
        "interactive_p95_ms": round(_percentile(latencies, 0.95), 3),
        "interactive_p99_ms": round(_percentile(latencies, 0.99), 3),
        "admission_accepted": accepted,
        "admission_reason": reason,
        "status": "ok",
    }


if __name__ == "__main__":
    print(json.dumps(run_spike(), indent=2))
