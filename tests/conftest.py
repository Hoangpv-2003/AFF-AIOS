"""Shared pytest fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.api.v1.endpoints.approvals import _APPROVALS
from app.core.config import Settings
from app.infrastructure.reconciliation.reconcile_service import reconciliation_service
from app.main import create_app
from app.skills.registry import registry


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


@pytest.fixture(autouse=True)
def reset_in_memory_state() -> None:
    _APPROVALS.clear()
    registry._skills.clear()
    reconciliation_service.reset()
