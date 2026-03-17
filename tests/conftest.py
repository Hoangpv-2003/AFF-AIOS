"""Shared pytest fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
def client(app) -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def fake_settings() -> Settings:
    return Settings(
        environment="test",
        debug=True,
        llm_provider="mock",
        vector_provider="chroma",
        queue_provider="redis_rq",
    )
