"""Dependency providers for FastAPI endpoints."""

from dataclasses import dataclass

from fastapi import Depends

from app.agents.coder import CoderAgent
from app.brain.planner import PlannerAgent
from app.core.config import Settings, get_settings
from app.core.security import AuthContext
from app.infrastructure.database.chroma_store import ChromaMemoryStore
from app.infrastructure.budget.enforcer import BudgetEnforcer
from app.infrastructure.queue.redis_rq_client import RedisRQQueueClient


@dataclass
class MockClient:
    provider: str


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
) -> RedisRQQueueClient:
    return RedisRQQueueClient()


def get_budget_enforcer(
    settings: Settings = Depends(get_settings_dep),
) -> BudgetEnforcer:
    return BudgetEnforcer(
        task_limit=settings.budget_task_limit,
        user_limit=settings.budget_user_limit,
        org_limit=settings.budget_org_limit,
    )


def get_planner_agent(
    budget_enforcer: BudgetEnforcer = Depends(get_budget_enforcer),
) -> PlannerAgent:
    return PlannerAgent(budget_enforcer=budget_enforcer)


def get_coder_agent(
    budget_enforcer: BudgetEnforcer = Depends(get_budget_enforcer),
) -> CoderAgent:
    return CoderAgent(budget_enforcer=budget_enforcer)


def get_auth_context() -> AuthContext:
    return AuthContext(subject="system", roles=["admin"])

