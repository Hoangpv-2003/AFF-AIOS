from app.agents.manager import ManagerAgent
from app.infrastructure.queue.redis_rq_client import RedisRQQueueClient


def test_queue_overload_degrades_predictably():
    queue_client = RedisRQQueueClient()
    queue_client.set_depth("interactive", 5001)

    manager = ManagerAgent(queue_client=queue_client)
    result = manager.run(task_id="chaos-q1", prompt="critical", priority="interactive")

    assert result.final_state == "FAILED"
    assert result.reason_code == "QUEUE_OVERLOADED"
    assert result.transitions == ["RECEIVED", "FAILED"]
