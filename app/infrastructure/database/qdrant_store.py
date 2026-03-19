"""Qdrant vector store adapter."""

from __future__ import annotations

import uuid
from typing import Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.brain.memory import MemoryQuery, MemoryRecord, MemorySearchResult


class QdrantMemoryStore:
    """Vector store implementation using Qdrant cloud/local."""

    def __init__(
        self,
        url: str,
        api_key: Optional[str] = None,
        collection_name: str = "aaf_memory",
        vector_size: int = 1024,  # Default for bge-m3
    ) -> None:
        self.url = url
        self.collection_name = collection_name
        self.client = QdrantClient(url=url, api_key=api_key, timeout=10.0)
        try:
            self._ensure_collection(vector_size)
        except Exception as e:
            print(f"WARNING: Qdrant collection check failed (timeout/conn): {e}")

    def _ensure_collection(self, vector_size: int) -> None:
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=vector_size, distance=models.Distance.COSINE
                    ),
                )
        except Exception as e:
             raise e


    def upsert(self, records: List[MemoryRecord]) -> None:
        points = []
        for rec in records:
            if not rec.embedding:
                continue
            points.append(
                models.PointStruct(
                    id=rec.id if self._is_valid_uuid(rec.id) else str(uuid.uuid4()),
                    vector=rec.embedding,
                    payload={
                        "text": rec.text,
                        "metadata": rec.metadata,
                        "created_at": rec.created_at,
                        "original_id": rec.id,
                    },
                )
            )
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )

    def search(self, query: MemoryQuery) -> List[MemorySearchResult]:
        if not query.embedding:
            return []

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query.embedding,
            limit=query.top_k,
            with_payload=True,
        ).points

        search_results = []
        for res in results:
            payload = res.payload or {}
            record = MemoryRecord(
                id=payload.get("original_id", str(res.id)),
                text=payload.get("text", ""),
                embedding=None,  # We don't usually need to return the embedding
                metadata=payload.get("metadata", {}),
                created_at=payload.get("created_at", 0.0),
            )
            search_results.append(
                MemorySearchResult(record=record, score=res.score)
            )
        return search_results

    def delete(self, record_ids: List[str]) -> int:
        # Note: This is an approximation since Qdrant delete is async
        result = self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="original_id",
                            match=models.MatchAny(any=record_ids),
                        )
                    ]
                )
            ),
        )
        return len(record_ids)

    def health(self) -> Dict[str, str]:
        try:
            self.client.get_collections()
            return {
                "status": "ok",
                "backend": "qdrant",
                "url": self.url,
                "collection": self.collection_name,
            }
        except Exception as e:
            return {"status": "error", "message": str(e), "backend": "qdrant"}

    @staticmethod
    def _is_valid_uuid(val: str) -> bool:
        try:
            uuid.UUID(str(val))
            return True
        except ValueError:
            return False
