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

    llm_provider: str = "mock"
    vector_provider: str = "chroma"
    queue_provider: str = "redis_rq"

    sandbox_offline_mode: bool = True
    interactive_queue_p95_ms_target: int = 500
    budget_task_limit: int = 100_000
    budget_user_limit: int = 1_000_000
    budget_org_limit: int = 10_000_000


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

