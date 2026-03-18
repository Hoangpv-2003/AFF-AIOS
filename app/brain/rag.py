"""RAG service to ingest and retrieve contextual memory for agents."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol

from app.brain.memory import MemoryQuery, MemoryRecord, MemorySearchResult, VectorMemoryStore


class EmbeddingClient(Protocol):
    def embed(self, text: str) -> List[float]:
        ...


@dataclass
class RAGService:
    vector_store: VectorMemoryStore
    embedding_client: EmbeddingClient

    def ingest(self, record_id: str, text: str, metadata: Optional[Dict[str, object]] = None) -> None:
        embedding = self.embedding_client.embed(text)
        record = MemoryRecord(
            id=record_id,
            text=text,
            embedding=embedding,
            metadata=dict(metadata or {}),
            created_at=time.time(),
        )
        self.vector_store.upsert([record])

    def retrieve(
        self,
        query_text: str,
        top_k: int = 3,
        filters: Optional[Dict[str, object]] = None,
    ) -> List[MemorySearchResult]:
        embedding = self.embedding_client.embed(query_text)
        query = MemoryQuery(
            query_text=query_text,
            top_k=top_k,
            embedding=embedding,
            filters=dict(filters or {}),
        )
        return self.vector_store.search(query)

    def build_context(self, query_text: str, top_k: int = 3) -> str:
        results = self.retrieve(query_text=query_text, top_k=top_k)
        if not results:
            return ""
        parts = []
        for index, item in enumerate(results, start=1):
            parts.append(f"[{index}] {item.record.text}")
        return "\n".join(parts)
