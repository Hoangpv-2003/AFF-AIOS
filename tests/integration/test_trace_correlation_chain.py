from app.agents.base_agent import AgentContext
from app.agents.reviewer import ReviewerAgent


def test_trace_correlation_chain_end_to_end(client):
    trace_id = "trace-integration-1"

    health = client.get("/health", headers={"X-Trace-Id": trace_id})
    assert health.status_code == 200
    assert health.headers.get("X-Trace-Id") == trace_id

    reviewer = ReviewerAgent()
    context = AgentContext(
        task_id="task-trace-1",
        trace_id=trace_id,
        prompt="review generated artifacts",
    )

    reviewer.think(context)
    act_result = reviewer.act(
        context,
        {
            "artifacts": {
                "files": ["skills/dynamic/trace_skill.py"],
                "rationale": "safe local run",
            }
        },
    )
    reviewer.observe(context, act_result)

    trace_response = client.get("/api/v1/traces", params={"trace_id": trace_id})
    assert trace_response.status_code == 200

    body = trace_response.json()
    assert body["trace_id"] == trace_id
    assert len(body["events"]) >= 4

    spans = [item for item in body["events"] if "name" in item and "span_id" in item]
    assert any(item["name"].startswith("http.") for item in spans)
    assert any(item["name"].startswith("agent.reviewer.think") for item in spans)
    assert any(item["name"].startswith("prompt.reviewer.think") for item in spans)
    assert any(item.get("parent_span_id") for item in spans)
