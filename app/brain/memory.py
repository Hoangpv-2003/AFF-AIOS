"""Memory contracts and local in-memory vector store implementation."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol


@dataclass
class MemoryRecord:
    """A stored memory item used by planner/coder retrieval."""

    id: str
    text: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


@dataclass
class MemoryQuery:
    """A retrieval query with optional filters and embedding."""

    query_text: str
    top_k: int = 5
    embedding: Optional[List[float]] = None
    filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemorySearchResult:
    """A scored memory retrieval result."""

    record: MemoryRecord
    score: float


class VectorMemoryStore(Protocol):
    """Provider-agnostic vector memory storage interface."""

    def upsert(self, records: List[MemoryRecord]) -> None:
        ...

    def search(self, query: MemoryQuery) -> List[MemorySearchResult]:
        ...

    def delete(self, record_ids: List[str]) -> int:
        ...

    def health(self) -> Dict[str, str]:
        ...


class InMemoryVectorStore:
    """Simple in-memory store for local development and tests."""

    def __init__(self) -> None:
        self._records: Dict[str, MemoryRecord] = {}

    def upsert(self, records: List[MemoryRecord]) -> None:
        for record in records:
            self._records[record.id] = record

    def search(self, query: MemoryQuery) -> List[MemorySearchResult]:
        candidates: List[MemoryRecord] = []
        for record in self._records.values():
            if self._matches_filters(record, query.filters):
                candidates.append(record)

        scored = [
            MemorySearchResult(record=record, score=self._score(record, query))
            for record in candidates
        ]
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[: query.top_k]

    def delete(self, record_ids: List[str]) -> int:
        deleted = 0
        for record_id in record_ids:
            if record_id in self._records:
                del self._records[record_id]
                deleted += 1
        return deleted

    def health(self) -> Dict[str, str]:
        return {
            "status": "ok",
            "backend": "in_memory",
            "records": str(len(self._records)),
        }

    @staticmethod
    def _matches_filters(record: MemoryRecord, filters: Dict[str, Any]) -> bool:
        if not filters:
            return True
        for key, expected in filters.items():
            if record.metadata.get(key) != expected:
                return False
        return True

    @staticmethod
    def _token_overlap(a: str, b: str) -> float:
        a_tokens = set(a.lower().split())
        b_tokens = set(b.lower().split())
        if not a_tokens or not b_tokens:
            return 0.0
        return len(a_tokens & b_tokens) / len(a_tokens | b_tokens)

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        if len(a) != len(b) or not a:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _score(self, record: MemoryRecord, query: MemoryQuery) -> float:
        if query.embedding and record.embedding:
            return self._cosine_similarity(record.embedding, query.embedding)
        return self._token_overlap(record.text, query.query_text)
