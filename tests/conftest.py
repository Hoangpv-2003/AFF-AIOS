"""Shared pytest fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.api.v1.endpoints.approvals import _APPROVALS
from app.api.v1.endpoints.tasks import _IDEMPOTENCY, _TASKS
from app.core.config import Settings
from app.infrastructure.budget.budget_ledger import budget_ledger
from app.infrastructure.budget.kill_switch import runtime_kill_switch
from app.infrastructure.observability.tracing import get_tracer
from app.infrastructure.reconciliation.reconcile_service import (
    reconciliation_service,
)
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
        vector_provider="chroma",
        queue_provider="redis_rq",
    )


@pytest.fixture(autouse=True)
def reset_in_memory_state() -> None:
    _APPROVALS.clear()
    _TASKS.clear()
    _IDEMPOTENCY.clear()
    registry._skills.clear()
    budget_ledger.clear()
    runtime_kill_switch.disable()
    reconciliation_service.reset()
    get_tracer().clear()
