from __future__ import annotations

import time

from app.brain.memory import InMemoryVectorStore
from app.brain.rag import RAGService


class TinyEmbeddingClient:
    def embed(self, text: str) -> list[float]:
        vec = [0.0, 0.0, 0.0, 0.0]
        for i, ch in enumerate(text.lower()):
            vec[i % 4] += float(ord(ch) % 31)
        norm = sum(abs(v) for v in vec) or 1.0
        return [v / norm for v in vec]


def test_retrieve_respects_filters_and_min_score():
    rag = RAGService(
        vector_store=InMemoryVectorStore(),
        embedding_client=TinyEmbeddingClient(),
    )
    rag.ingest("a", "build auth endpoint", {"type": "tech"})
    rag.ingest("b", "cook noodle soup", {"type": "food"})

    res = rag.retrieve("auth endpoint", top_k=5, filters={"type": "tech"}, min_score=0.01)

    assert len(res) >= 1
    assert all(item.record.metadata.get("type") == "tech" for item in res)


def test_build_context_deduplicates_and_limits_size():
    rag = RAGService(
        vector_store=InMemoryVectorStore(),
        embedding_client=TinyEmbeddingClient(),
        max_context_chars=120,
        max_item_chars=60,
    )
    rag.ingest("1", "Implement login API with JWT and tests", {"type": "plan"})
    rag.ingest("2", "Implement login API with JWT and tests", {"type": "dup"})
    rag.ingest("3", "Add refresh token flow and security checks", {"type": "plan"})

    context = rag.build_context("login api", top_k=5)

    assert context.count("Implement login API") == 1
    assert len(context) <= 120


def test_recency_boost_prefers_newer_when_relevance_close():
    rag = RAGService(
        vector_store=InMemoryVectorStore(),
        embedding_client=TinyEmbeddingClient(),
        min_score=0.0,
    )
    rag.ingest("old", "release checklist with ci", {"type": "ops"})
    time.sleep(0.01)
    rag.ingest("new", "release checklist with ci", {"type": "ops"})

    results = rag.retrieve(
        "release checklist",
        top_k=2,
        min_score=0.0,
        deduplicate=False,
    )

    assert len(results) == 2
    assert results[0].record.id == "new"
