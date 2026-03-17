from app.agents.manager import ManagerAgent
from app.infrastructure.queue.redis_rq_client import RedisRQQueueClient


def test_backpressure_admission_rejects_overloaded_standard_queue():
    queue = RedisRQQueueClient()
    queue.set_depth("standard", 1001)

    manager = ManagerAgent(queue_client=queue)
    accepted, reason = manager.evaluate_admission("standard")

    assert accepted is False
    assert reason == "QUEUE_OVERLOADED"


def test_manager_run_fails_fast_when_admission_rejects():
    queue = RedisRQQueueClient()
    queue.set_depth("batch", 501)

    manager = ManagerAgent(queue_client=queue)
    result = manager.run(
        task_id="bp-1",
        prompt="process data",
        priority="batch",
    )

    assert result.final_state == "FAILED"
    assert result.reason_code == "QUEUE_OVERLOADED"
