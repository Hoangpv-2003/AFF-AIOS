"""Dependency providers for FastAPI endpoints."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import Depends
from fastapi.params import Depends as DependsClass

from app.agents.coder import CoderAgent
from app.agents.reviewer import ReviewerAgent
from app.agents.intent_parser import IntentParserAgent
from app.agents.clarifier import ClarifierAgent
from app.agents.skill_router import SkillRouterAgent
from app.agents.result_validator import ResultValidatorAgent
from app.agents.orchestrator import OrchestratorAgent
from app.agents.error_handler import ErrorHandlerAgent
from app.agents.context_injector import ContextInjectorAgent
from app.agents.synthesizer import SynthesizerAgent
from app.agents.manager import ManagerAgent
from app.brain.rag import EmbeddingClient, RAGService
from app.brain.planner import PlannerAgent
from app.core.config import Settings, get_settings
from app.core.security import AuthContext
from app.infrastructure.database.chroma_store import ChromaMemoryStore
from app.infrastructure.database.qdrant_store import QdrantMemoryStore
from app.infrastructure.database.mongodb_store import MongoDBStore
from app.infrastructure.budget.enforcer import BudgetEnforcer
from app.infrastructure.external_apis.ollama_client import (
    OllamaEmbeddingClient,
    OllamaLLMClient,
)
from app.infrastructure.queue.redis_rq_client import RedisRQQueueClient
from app.infrastructure.queue.redis_rq_real_client import RedisRQRealClient
from app.brain.memory_manager import MemoryManager


_VECTOR_STORES: Dict[str, Any] = {}
_RAG_SERVICES: Dict[str, RAGService] = {}
_MONGODB_STORES: Dict[str, MongoDBStore] = {}


def get_settings_dep() -> Settings:
    return get_settings()


def get_llm_client(
    settings: Settings = None,
    model_name: Optional[str] = None,
) -> OllamaLLMClient:
    if settings is None or isinstance(settings, DependsClass):
        settings = get_settings()
    return OllamaLLMClient(
        base_url=settings.ollama_base_url,
        primary_model=model_name or settings.ollama_chat_model,
        fallback_models=[],
    )


def get_agent_llm_client(
    settings: Settings = None,
) -> OllamaLLMClient:
    if settings is None or isinstance(settings, DependsClass):
        settings = get_settings()
    return get_llm_client(settings, model_name=settings.ollama_agent_model)


def get_coder_llm_client(
    settings: Settings = None,
) -> OllamaLLMClient:
    if settings is None or isinstance(settings, DependsClass):
        settings = get_settings()
    return get_llm_client(settings, model_name=settings.ollama_coder_model)


def get_reviewer_llm_client(
    settings: Settings = None,
) -> OllamaLLMClient:
    if settings is None or isinstance(settings, DependsClass):
        settings = get_settings()
    return get_llm_client(settings, model_name=settings.ollama_reviewer_model)


def get_embedding_client(
    settings: Any = None,
) -> Any:
    if settings is None or isinstance(settings, DependsClass):
        settings = get_settings()
    return OllamaEmbeddingClient(
        base_url=settings.ollama_base_url,
        embedding_model=settings.ollama_embedding_model,
    )


def get_vector_store(
    settings: Settings = None,
) -> Any:
    if settings is None or isinstance(settings, DependsClass):
        settings = get_settings()
    key = f"{settings.environment}:{settings.vector_provider}"
    if key not in _VECTOR_STORES:
        if not settings.demo_mode and settings.qdrant_url:
            _VECTOR_STORES[key] = QdrantMemoryStore(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
                collection_name=f"aaf_{settings.environment}",
            )
        else:
            _VECTOR_STORES[key] = ChromaMemoryStore(
                collection_name=f"aaf_{settings.environment}"
            )
    return _VECTOR_STORES[key]


def get_rag_service(
    settings: Any = None,
    vector_store: Any = None,
    embedding_client: Any = None,
) -> Any:
    if settings is None or isinstance(settings, DependsClass):
        settings = get_settings()
    if vector_store is None or isinstance(vector_store, DependsClass):
        vector_store = get_vector_store(settings)
    if embedding_client is None or isinstance(embedding_client, DependsClass):
        embedding_client = get_embedding_client(settings)
        
    key = f"{settings.environment}:ollama:{settings.vector_provider}"
    if key not in _RAG_SERVICES:
        _RAG_SERVICES[key] = RAGService(
            vector_store=vector_store,
            embedding_client=embedding_client,
        )
    return _RAG_SERVICES[key]


def get_queue_client(
    settings: Settings = Depends(get_settings_dep),
) -> Any:
    if not settings.demo_mode and settings.redis_url:
        return RedisRQRealClient(redis_url=settings.redis_url)
    return RedisRQQueueClient()


def get_mongodb_store(
    settings: Settings = Depends(get_settings_dep),
) -> Optional[MongoDBStore]:
    if not settings.mongodb_uri:
        return None
    key = f"{settings.environment}:{settings.mongodb_db}"
    if key not in _MONGODB_STORES:
        _MONGODB_STORES[key] = MongoDBStore(
            uri=settings.mongodb_uri,
            db_name=settings.mongodb_db,
        )
    return _MONGODB_STORES[key]


def get_memory_manager(
    rag_service: Any = Depends(get_rag_service),
    mongodb_store: Optional[MongoDBStore] = Depends(get_mongodb_store),
) -> MemoryManager:
    from app.brain.memory_manager import MemoryManager
    return MemoryManager(rag_service, mongodb_store)


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
    llm_client: OllamaLLMClient = Depends(get_agent_llm_client),
    rag_service: Any = Depends(get_rag_service),
) -> PlannerAgent:
    return PlannerAgent(
        budget_enforcer=budget_enforcer,
        llm_client=llm_client,
        rag_service=rag_service,
    )


def get_coder_agent(
    budget_enforcer: BudgetEnforcer = Depends(get_budget_enforcer),
    llm_client: OllamaLLMClient = Depends(get_coder_llm_client),
    rag_service: Any = Depends(get_rag_service),
) -> CoderAgent:
    return CoderAgent(
        budget_enforcer=budget_enforcer,
        llm_client=llm_client,
        rag_service=rag_service,
    )


def get_reviewer_agent(
    llm_client: OllamaLLMClient = Depends(get_reviewer_llm_client),
) -> ReviewerAgent:
    from app.agents.reviewer import ReviewerAgent
    return ReviewerAgent(llm_client=llm_client)


def get_intent_parser_agent(
    llm_client: OllamaLLMClient = Depends(get_agent_llm_client),
) -> IntentParserAgent:
    return IntentParserAgent(llm_client=llm_client)


def get_clarifier_agent(
    llm_client: OllamaLLMClient = Depends(get_agent_llm_client),
) -> ClarifierAgent:
    return ClarifierAgent(llm_client=llm_client)


def get_skill_router_agent(
    llm_client: OllamaLLMClient = Depends(get_agent_llm_client),
) -> SkillRouterAgent:
    return SkillRouterAgent(llm_client=llm_client)


def get_result_validator_agent(
    llm_client: OllamaLLMClient = Depends(get_agent_llm_client),
) -> ResultValidatorAgent:
    return ResultValidatorAgent(llm_client=llm_client)


def get_error_handler_agent(
    llm_client: OllamaLLMClient = Depends(get_agent_llm_client),
) -> ErrorHandlerAgent:
    return ErrorHandlerAgent(llm_client=llm_client)


def get_orchestrator_agent(
    llm_client: OllamaLLMClient = Depends(get_agent_llm_client),
) -> OrchestratorAgent:
    return OrchestratorAgent(llm_client=llm_client)


def get_context_injector_agent(
    llm_client: OllamaLLMClient = Depends(get_agent_llm_client),
) -> ContextInjectorAgent:
    return ContextInjectorAgent(llm_client=llm_client)


def get_synthesizer_agent(
    llm_client: OllamaLLMClient = Depends(get_agent_llm_client),
) -> SynthesizerAgent:
    return SynthesizerAgent(llm_client=llm_client)


def get_manager_agent(
    llm_client: OllamaLLMClient = Depends(get_agent_llm_client),
    context_injector: ContextInjectorAgent = Depends(get_context_injector_agent),
    intent_parser: IntentParserAgent = Depends(get_intent_parser_agent),
    clarifier: ClarifierAgent = Depends(get_clarifier_agent),
    planner: PlannerAgent = Depends(get_planner_agent),
    router: SkillRouterAgent = Depends(get_skill_router_agent),
    orchestrator: OrchestratorAgent = Depends(get_orchestrator_agent),
    coder: CoderAgent = Depends(get_coder_agent),
    reviewer: ReviewerAgent = Depends(get_reviewer_agent),
    validator: ResultValidatorAgent = Depends(get_result_validator_agent),
    synthesizer: SynthesizerAgent = Depends(get_synthesizer_agent),
) -> ManagerAgent:
    return ManagerAgent(
        llm_client=llm_client,
        context_injector=context_injector,
        intent_parser=intent_parser,
        clarifier=clarifier,
        planner=planner,
        router=router,
        orchestrator=orchestrator,
        coder=coder,
        reviewer=reviewer,
        validator=validator,
        synthesizer=synthesizer,
    )


def get_auth_context() -> AuthContext:
    return AuthContext(subject="system", roles=["admin"])
