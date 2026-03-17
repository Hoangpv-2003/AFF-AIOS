def test_task_create_idempotency(client):
    payload = {"prompt": "create skill", "priority": "standard"}
    headers = {"Idempotency-Key": "idem-1"}

    first = client.post("/api/v1/tasks", json=payload, headers=headers)
    second = client.post("/api/v1/tasks", json=payload, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["task_id"] == second.json()["task_id"]
