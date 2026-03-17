"""Pinecone vector store adapter placeholder.

This adapter currently reuses in-memory behavior for interface compatibility.
"""

from __future__ import annotations

from typing import Dict, List

from app.brain.memory import InMemoryVectorStore, MemoryQuery, MemoryRecord, MemorySearchResult


class PineconeMemoryStore:
    """Interface-compatible placeholder until production Pinecone integration."""

    def __init__(self, index_name: str = "aaf-memory") -> None:
        self.index_name = index_name
        self._store = InMemoryVectorStore()

    def upsert(self, records: List[MemoryRecord]) -> None:
        self._store.upsert(records)

    def search(self, query: MemoryQuery) -> List[MemorySearchResult]:
        return self._store.search(query)

    def delete(self, record_ids: List[str]) -> int:
        return self._store.delete(record_ids)

    def health(self) -> Dict[str, str]:
        health = self._store.health()
        health["backend"] = "pinecone_adapter_local"
        health["index"] = self.index_name
        return health
