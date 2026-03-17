"""Chroma vector store adapter.

This adapter uses local in-memory fallback for current milestone.
"""

from __future__ import annotations

from typing import Dict, List

from app.brain.memory import InMemoryVectorStore, MemoryQuery, MemoryRecord, MemorySearchResult


class ChromaMemoryStore:
    """Provider-compatible adapter for local Chroma development path."""

    def __init__(self, collection_name: str = "aaf_memory") -> None:
        self.collection_name = collection_name
        self._store = InMemoryVectorStore()

    def upsert(self, records: List[MemoryRecord]) -> None:
        self._store.upsert(records)

    def search(self, query: MemoryQuery) -> List[MemorySearchResult]:
        return self._store.search(query)

    def delete(self, record_ids: List[str]) -> int:
        return self._store.delete(record_ids)

    def health(self) -> Dict[str, str]:
        health = self._store.health()
        health["backend"] = "chroma_adapter_local"
        health["collection"] = self.collection_name
        return health
