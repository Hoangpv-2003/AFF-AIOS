def test_draft_task_payload_remains_accepted(client):
    response = client.post(
        "/api/v1/tasks",
        json={"prompt": "legacy client payload", "priority": "standard"},
        headers={"X-AAF-Schema": "draft"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["task_id"].startswith("task-")
    assert body["state"] == "RECEIVED"
