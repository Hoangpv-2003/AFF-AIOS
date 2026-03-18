"""Dependency providers for FastAPI endpoints."""

from __future__ import annotations

from typing import Dict, List

from fastapi import Depends

from app.agents.coder import CoderAgent
from app.brain.rag import EmbeddingClient, RAGService
from app.brain.planner import PlannerAgent
from app.core.config import Settings, get_settings
from app.core.security import AuthContext
from app.infrastructure.database.chroma_store import ChromaMemoryStore
from app.infrastructure.budget.enforcer import BudgetEnforcer
from app.infrastructure.external_apis.ollama_client import (
    OllamaEmbeddingClient,
    OllamaLLMClient,
)
from app.infrastructure.queue.redis_rq_client import RedisRQQueueClient


_VECTOR_STORES: Dict[str, ChromaMemoryStore] = {}
_RAG_SERVICES: Dict[str, RAGService] = {}


def _parse_fallback_models(raw: str) -> List[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def get_settings_dep() -> Settings:
    return get_settings()


def get_llm_client(
    settings: Settings = Depends(get_settings_dep),
) -> OllamaLLMClient:
    return OllamaLLMClient(
        base_url=settings.ollama_base_url,
        primary_model=settings.ollama_chat_model,
        fallback_models=_parse_fallback_models(
            settings.ollama_fallback_models
        ),
    )


def get_embedding_client(
    settings: Settings = Depends(get_settings_dep),
) -> EmbeddingClient:
    return OllamaEmbeddingClient(
        base_url=settings.ollama_base_url,
        embedding_model=settings.ollama_embedding_model,
    )


def get_vector_store(
    settings: Settings = Depends(get_settings_dep),
) -> ChromaMemoryStore:
    key = f"{settings.environment}:{settings.vector_provider}"
    if key not in _VECTOR_STORES:
        _VECTOR_STORES[key] = ChromaMemoryStore(
            collection_name=f"aaf_{settings.environment}"
        )
    return _VECTOR_STORES[key]


def get_rag_service(
    settings: Settings = Depends(get_settings_dep),
    vector_store: ChromaMemoryStore = Depends(get_vector_store),
    embedding_client: EmbeddingClient = Depends(get_embedding_client),
) -> RAGService:
    key = f"{settings.environment}:ollama:{settings.vector_provider}"
    if key not in _RAG_SERVICES:
        _RAG_SERVICES[key] = RAGService(
            vector_store=vector_store,
            embedding_client=embedding_client,
        )
    return _RAG_SERVICES[key]


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
    llm_client: OllamaLLMClient = Depends(get_llm_client),
    rag_service: RAGService = Depends(get_rag_service),
) -> PlannerAgent:
    return PlannerAgent(
        budget_enforcer=budget_enforcer,
        llm_client=llm_client,
        rag_service=rag_service,
    )


def get_coder_agent(
    budget_enforcer: BudgetEnforcer = Depends(get_budget_enforcer),
    llm_client: OllamaLLMClient = Depends(get_llm_client),
    rag_service: RAGService = Depends(get_rag_service),
) -> CoderAgent:
    return CoderAgent(
        budget_enforcer=budget_enforcer,
        llm_client=llm_client,
        rag_service=rag_service,
    )


def get_auth_context() -> AuthContext:
    return AuthContext(subject="system", roles=["admin"])
