"""RAG service to ingest and retrieve contextual memory for agents."""

from __future__ import annotations

import re
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

    # Retrieval quality knobs (tuned for stable default behavior)
    min_score: float = 0.05
    recency_half_life_sec: float = 60 * 60 * 24 * 7  # 7 days
    max_context_chars: int = 2400
    max_item_chars: int = 450

    @staticmethod
    def _normalize_text(text: str) -> str:
        lowered = text.lower().strip()
        lowered = re.sub(r"\s+", " ", lowered)
        return lowered

    @staticmethod
    def _safe_metadata(metadata: Optional[Dict[str, object]]) -> Dict[str, object]:
        if not metadata:
            return {}
        return dict(metadata)

    def _blend_score(self, score: float, created_at: float) -> float:
        # Lightweight freshness boost keeps recent relevant memories on top.
        age = max(0.0, time.time() - float(created_at))
        freshness = 0.5 ** (age / max(1.0, self.recency_half_life_sec))
        return (0.9 * score) + (0.1 * freshness)

    def _deduplicate(self, items: List[MemorySearchResult]) -> List[MemorySearchResult]:
        by_id: set[str] = set()
        by_text: set[str] = set()
        deduped: List[MemorySearchResult] = []
        for item in items:
            record = item.record
            if record.id in by_id:
                continue
            key = self._normalize_text(record.text)
            if key in by_text:
                continue
            by_id.add(record.id)
            by_text.add(key)
            deduped.append(item)
        return deduped

    def ingest(self, record_id: str, text: str, metadata: Optional[Dict[str, object]] = None) -> None:
        normalized_text = self._normalize_text(text)
        embedding = self.embedding_client.embed(normalized_text)
        record = MemoryRecord(
            id=record_id,
            text=text.strip(),
            embedding=embedding,
            metadata=self._safe_metadata(metadata),
            created_at=time.time(),
        )
        self.vector_store.upsert([record])

    def retrieve(
        self,
        query_text: str,
        top_k: int = 3,
        filters: Optional[Dict[str, object]] = None,
        min_score: Optional[float] = None,
        deduplicate: bool = True,
        use_recency_boost: bool = True,
    ) -> List[MemorySearchResult]:
        normalized_query = self._normalize_text(query_text)
        embedding = self.embedding_client.embed(normalized_query)
        recency_boost = 0.15 if use_recency_boost else 0.0
        query = MemoryQuery(
            query_text=normalized_query,
            top_k=max(top_k * 4, top_k),
            embedding=embedding,
            filters=dict(filters or {}),
            min_score=self.min_score if min_score is None else float(min_score),
            deduplicate=deduplicate,
            recency_boost=recency_boost,
        )
        raw = self.vector_store.search(query)
        if use_recency_boost:
            boosted: List[MemorySearchResult] = []
            for item in raw:
                boosted.append(
                    MemorySearchResult(
                        record=item.record,
                        score=self._blend_score(float(item.score), item.record.created_at),
                    )
                )
            boosted.sort(key=lambda x: x.score, reverse=True)
            raw = boosted
        return raw[:top_k]

    def build_context(
        self,
        query_text: str,
        top_k: int = 3,
        filters: Optional[Dict[str, object]] = None,
        include_metadata: bool = False,
        max_chars: Optional[int] = None,
    ) -> str:
        results = self.retrieve(
            query_text=query_text,
            top_k=top_k,
            filters=filters,
        )
        if not results:
            return ""

        char_limit = self.max_context_chars if max_chars is None else int(max_chars)
        parts = []
        current_len = 0
        for index, item in enumerate(results, start=1):
            text = item.record.text.strip()
            if len(text) > self.max_item_chars:
                text = text[: self.max_item_chars - 3].rstrip() + "..."
            head = f"[{index}]"
            if include_metadata and item.record.metadata:
                head += f" ({item.record.metadata})"
            line = f"{head} {text}"
            if current_len + len(line) + 1 > char_limit:
                break
            parts.append(line)
            current_len += len(line) + 1
        return "\n".join(parts)

    def build_grouped_context(
        self,
        query_text: str,
        user_id: Optional[str] = None,
        facts_top_k: int = 3,
        chats_top_k: int = 4,
    ) -> str:
        base_filter: Dict[str, object] = {}
        if user_id:
            base_filter["user_id"] = user_id

        fact_filters = dict(base_filter)
        fact_filters["type"] = "fact"
        chat_filters = dict(base_filter)
        chat_filters["type"] = "chat"

        facts = self.build_context(
            query_text=query_text,
            top_k=facts_top_k,
            filters=fact_filters,
            include_metadata=False,
            max_chars=max(600, self.max_context_chars // 2),
        )
        chats = self.build_context(
            query_text=query_text,
            top_k=chats_top_k,
            filters=chat_filters,
            include_metadata=False,
            max_chars=max(900, self.max_context_chars // 2),
        )

        sections = [
            "## Long-term Facts",
            facts or "No facts found.",
            "",
            "## Relevant Chat History",
            chats or "No relevant history.",
        ]
        return "\n".join(sections)
