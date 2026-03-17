def test_activation_requires_valid_approval(client):
    submit = client.post(
        "/api/v1/approvals/submit",
        json={
            "task_id": "t-approval",
            "skill_id": "skill-1",
            "requested_by": "tester",
            "reason": "initial approval",
        },
    )
    assert submit.status_code == 200
    approval_id = submit.json()["approval_id"]

    register = client.post(
        "/api/v1/skills/register",
        json={
            "skill_id": "skill-1",
            "version": "0.1.0",
            "digest": {"algorithm": "sha256", "value": "abc"},
            "source_task_id": "t-approval",
            "approval_id": approval_id,
            "status": "approved",
        },
    )
    assert register.status_code == 200

    blocked = client.post("/api/v1/skills/skill-1/activate")
    assert blocked.status_code == 400

    decision = client.post(
        f"/api/v1/approvals/{approval_id}/decision",
        params={"decision": "approve"},
    )
    assert decision.status_code == 200

    activated = client.post("/api/v1/skills/skill-1/activate")
    assert activated.status_code == 200
    assert activated.json()["state"] == "active"


def test_approval_expire_and_escalate_flow(client):
    submit = client.post(
        "/api/v1/approvals/submit",
        json={
            "task_id": "t-expire",
            "skill_id": "skill-2",
            "requested_by": "tester",
        },
    )
    approval_id = submit.json()["approval_id"]

    expired = client.post(f"/api/v1/approvals/{approval_id}/expire")
    assert expired.status_code == 200
    assert expired.json()["status"] == "expired"

    escalated = client.post(f"/api/v1/approvals/{approval_id}/escalate")
    assert escalated.status_code == 200
    assert escalated.json()["status"] == "escalated"
    assert escalated.json()["escalated_to"] == "fallback_reviewer"
