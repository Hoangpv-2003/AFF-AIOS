def test_draft_mode_emits_deprecation_and_migration_headers(client):
    response = client.post(
        "/api/v1/tasks",
        json={"prompt": "migrate me", "priority": "interactive"},
        headers={"X-AAF-Schema": "draft"},
    )

    assert response.status_code == 200
    assert response.headers.get("Deprecation") == "true"
    assert response.headers.get("Sunset") is not None
    assert response.headers.get("X-AAF-Migration") == "draft->stable"


def test_stable_mode_does_not_emit_draft_deprecation_headers(client):
    response = client.post(
        "/api/v1/tasks",
        json={"prompt": "stable payload", "priority": "batch"},
    )

    assert response.status_code == 200
    assert response.headers.get("Deprecation") is None
    assert response.headers.get("X-AAF-Migration") is None
