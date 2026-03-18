from app.api import dependencies
from app.brain.rag import RAGService
from app.core.config import Settings
from app.infrastructure.external_apis.ollama_client import (
    OllamaEmbeddingClient,
    OllamaLLMClient,
)


def test_llm_client_uses_ollama_defaults():
    settings = Settings()

    client = dependencies.get_llm_client(settings)

    assert isinstance(client, OllamaLLMClient)


def test_llm_client_uses_ollama_with_fallback_models():
    settings = Settings(
        ollama_base_url="http://127.0.0.1:11434",
        ollama_chat_model="qwen3:8b",
        ollama_fallback_models="llama3.1:8b,qwen3:0.5b",
    )

    client = dependencies.get_llm_client(settings)

    assert isinstance(client, OllamaLLMClient)
    assert client.primary_model == "qwen3:8b"
    assert client.fallback_models == ["llama3.1:8b", "qwen3:0.5b"]


def test_embedding_client_uses_ollama_when_provider_is_ollama():
    settings = Settings(ollama_embedding_model="bge-m3:latest")

    client = dependencies.get_embedding_client(settings)

    assert isinstance(client, OllamaEmbeddingClient)
    assert client.embedding_model == "bge-m3:latest"


def test_rag_service_is_reused_for_same_dependency_key():
    dependencies._RAG_SERVICES.clear()
    dependencies._VECTOR_STORES.clear()
    settings = Settings(environment="dev", vector_provider="chroma")

    vector_store = dependencies.get_vector_store(settings)
    embedding_client = dependencies.get_embedding_client(settings)
    rag_one = dependencies.get_rag_service(
        settings,
        vector_store,
        embedding_client,
    )
    rag_two = dependencies.get_rag_service(
        settings,
        vector_store,
        embedding_client,
    )

    assert isinstance(rag_one, RAGService)
    assert rag_one is rag_two
