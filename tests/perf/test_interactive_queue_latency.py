import time

from app.agents.manager import ManagerAgent
from app.infrastructure.queue.redis_rq_client import RedisRQQueueClient


def _percentile(values, q):
    ordered = sorted(values)
    idx = int((len(ordered) - 1) * q)
    return ordered[idx]


def test_interactive_queue_latency_under_load():
    queue = RedisRQQueueClient()

    # Simulate background batch backlog while interactive requests arrive.
    queue.set_depth("batch", 100)

    latencies_ms = []
    for i in range(20):
        start = time.perf_counter()
        queue.submit("interactive", {"task_id": f"i-{i}"})
        latencies_ms.append((time.perf_counter() - start) * 1000)

    p95 = _percentile(latencies_ms, 0.95)
    assert p95 < 500

    manager = ManagerAgent(queue_client=queue)
    accepted, reason = manager.evaluate_admission("interactive")
    assert accepted is True
    assert reason == "ACCEPTED"
