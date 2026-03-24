"""Configuration models and settings loader."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    """Runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "AAF-AIOS"
    environment: str = Field(
        default="dev",
        description="Runtime environment: dev/offline/prod",
    )
    debug: bool = False

    api_prefix: str = "/api/v1"
    timezone: str = "Asia/Ho_Chi_Minh"
    locale: str = "vi-VN"

    demo_mode: bool = True

    # [V2.0 SYSTEM CONSTANTS]
    # Execution Loop Constraints
    MAX_VALIDATOR_RETRIES: int = 2
    MAX_PLANNER_ITERATIONS: int = 3
    MAX_CODE_REVIEW_ROUNDS: int = 3
    MAX_CONCURRENT_TASKS: int = 3
    
    # Confidence Thresholds
    CONFIDENCE_INTENT: float = 0.75
    CONFIDENCE_VALIDATION: float = 0.80
    CONFIDENCE_CODE_QUALITY: float = 0.85

    # Timeout Constraints
    TIMEOUT_REALTIME_FETCH: int = 10
    TIMEOUT_CODE_REVIEW: int = 10
    TIMEOUT_TOOL_EXEC_DEFAULT: int = 30
    TIMEOUT_USER_INTERACTION: int = 300

    # Backoff Strategy
    RETRY_INITIAL_DELAY: float = 0.5
    RETRY_MULTIPLIER: float = 2.0
    RETRY_MAX_DELAY: float = 30.0
    RETRY_JITTER: float = 0.1
    RETRY_MAX_TOTAL_WAIT: float = 120.0

    database_url: str = "sqlite:///./agentic.db"
    mongodb_uri: str = ""
    mongodb_db: str = "agentic"
    redis_url: str = ""
    qdrant_url: str = ""
    qdrant_api_key: str = ""

    keycloak_url: str = ""
    opa_url: str = ""
    vault_url: str = ""

    vector_provider: str = "chroma"
    queue_provider: str = "redis_rq"
    short_memory_ttl_seconds: int = 3600

    search_provider: str = "tavily"
    tavily_api_key: str = ""
    serpapi_api_key: str = ""

    email_provider: str = "resend"
    resend_api_key: str = ""
    resend_from_email: str = "onboarding@resend.dev"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_use_tls: bool = True
    allow_smtp_fallback: bool = False

    calendar_provider: str = "local"
    google_calendar_access_token: str = ""
    google_calendar_id: str = "primary"
    microsoft_graph_access_token: str = ""
    microsoft_tenant_id: str = ""
    microsoft_client_id: str = ""
    microsoft_client_secret: str = ""
    microsoft_calendar_user_id: str = ""
    microsoft_calendar_id: str = "primary"

    celery_broker_url: str = "amqp://guest:guest@localhost:5672//"
    celery_backend_url: str = "rpc://"

    openai_model: str = "qwen3:8b"
    openai_base_url: str = "http://localhost:11434/v1"
    openai_api_key: str = "ollama"

    langsmith_project: str = "agentic-system"
    langchain_api_key: str = ""
    langchain_tracing_v2: bool = False
    helicone_api_key: str = ""
    helicone_base_url: str = "https://oai.helicone.ai/v1"
    helicone_enabled: bool = False

    llm_model: str = "qwen3:8b"
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "qwen3:8b"
    ollama_agent_model: str = "llama3.1:8b"
    ollama_coder_model: str = "qwen3:8b"
    ollama_reviewer_model: str = "llama3.1:8b"
    ollama_fallback_models: str = ""
    ollama_embedding_model: str = "bge-m3:latest"

    existing_skill_reuse_score_threshold: float = 0.70
    cli_skill_reuse_score_threshold: float = 0.55

    sandbox_offline_mode: bool = True
    interactive_queue_p95_ms_target: int = 500
    budget_task_limit: int = 100_000
    budget_user_limit: int = 1_000_000
    budget_org_limit: int = 10_000_000


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
