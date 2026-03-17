def test_skill_drift_is_quarantined_and_cannot_execute(client):
    submit = client.post(
        "/api/v1/approvals/submit",
        json={
            "task_id": "task-drift",
            "skill_id": "skill-drift",
            "requested_by": "tester",
        },
    )
    approval_id = submit.json()["approval_id"]

    decide = client.post(
        f"/api/v1/approvals/{approval_id}/decision",
        params={"decision": "approve"},
    )
    assert decide.status_code == 200

    register = client.post(
        "/api/v1/skills/register",
        json={
            "skill_id": "skill-drift",
            "version": "0.1.0",
            "digest": {"algorithm": "sha256", "value": "digest-registry"},
            "source_task_id": "task-drift",
            "approval_id": approval_id,
            "status": "approved",
        },
    )
    assert register.status_code == 200

    activate = client.post("/api/v1/skills/skill-drift/activate")
    assert activate.status_code == 200
    assert activate.json()["state"] == "active"

    runtime_seed = client.post(
        "/api/v1/skills/reconciliation/seed/runtime/skill-drift",
        params={"digest": "digest-runtime-different"},
    )
    assert runtime_seed.status_code == 200

    git_seed = client.post(
        "/api/v1/skills/reconciliation/seed/git/skill-drift",
        params={"digest": "digest-registry"},
    )
    assert git_seed.status_code == 200

    reconcile = client.post("/api/v1/skills/reconciliation/run")
    assert reconcile.status_code == 200
    body = reconcile.json()
    assert body["drift_count"] == 1
    assert "skill-drift" in body["quarantined_skills"]

    skill = client.get("/api/v1/skills/skill-drift")
    assert skill.status_code == 200
    assert skill.json()["state"] == "quarantined"

    execute = client.post("/api/v1/skills/skill-drift/execute")
    assert execute.status_code == 423
