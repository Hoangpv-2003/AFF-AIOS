"""Dependency providers for FastAPI endpoints."""

from dataclasses import dataclass

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.core.security import AuthContext
from app.infrastructure.database.chroma_store import ChromaMemoryStore


@dataclass
class MockClient:
    provider: str


@dataclass
class BudgetEnforcer:
    task_limit: int
    user_limit: int
    org_limit: int

    def check(self, tokens: int) -> bool:
        return (
            tokens <= self.task_limit
            and tokens <= self.user_limit
            and tokens <= self.org_limit
        )


def get_settings_dep() -> Settings:
    return get_settings()


def get_llm_client(
    settings: Settings = Depends(get_settings_dep),
) -> MockClient:
    return MockClient(provider=settings.llm_provider)


def get_vector_store(
    settings: Settings = Depends(get_settings_dep),
) -> ChromaMemoryStore:
    return ChromaMemoryStore(collection_name=f"aaf_{settings.environment}")


def get_queue_client(
    settings: Settings = Depends(get_settings_dep),
) -> MockClient:
    return MockClient(provider=settings.queue_provider)


def get_budget_enforcer(
    settings: Settings = Depends(get_settings_dep),
) -> BudgetEnforcer:
    return BudgetEnforcer(
        task_limit=settings.budget_task_limit,
        user_limit=settings.budget_user_limit,
        org_limit=settings.budget_org_limit,
    )


def get_auth_context() -> AuthContext:
    return AuthContext(subject="system", roles=["admin"])

