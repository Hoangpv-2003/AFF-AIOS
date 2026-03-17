from app.infrastructure.budget.kill_switch import runtime_kill_switch


def test_runtime_kill_switch_blocks_and_unblocks_requests(client):
    baseline = client.post(
        "/api/v1/tasks",
        json={"prompt": "baseline", "priority": "standard"},
    )
    assert baseline.status_code == 200

    runtime_kill_switch.enable("ops_maintenance")

    blocked = client.post(
        "/api/v1/tasks",
        json={"prompt": "should be blocked", "priority": "standard"},
    )
    assert blocked.status_code == 503
    assert "ops_maintenance" in blocked.json()["detail"]

    runtime_kill_switch.disable()

    resumed = client.post(
        "/api/v1/tasks",
        json={"prompt": "service resumed", "priority": "standard"},
    )
    assert resumed.status_code == 200
