def test_not_found_uses_default_fastapi_error(client):
    response = client.get("/api/v1/tasks/non-existent")
    assert response.status_code == 404
    body = response.json()
    assert "detail" in body
