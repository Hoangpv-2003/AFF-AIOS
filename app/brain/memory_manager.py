from __future__ import annotations

import hashlib
import time
import uuid
from contextlib import contextmanager
from typing import Optional

from app.brain.rag import RAGService
from app.infrastructure.database.mongodb_store import MongoDBStore


class MemoryManager:
    """Manages short/long-term memory with MongoDB and RAG backends."""

    def __init__(
        self,
        rag_service: RAGService,
        mongodb: Optional[MongoDBStore] = None,
    ):
        self.rag = rag_service
        self.mongodb = mongodb
        self.chat_collection = "chat_history"
        self.fact_collection = "facts"

    @contextmanager
    def _use_collection(self, collection_name: str):
        if not self.mongodb:
            yield
            return
        original_name = self.mongodb.collection_name
        original_collection = self.mongodb.collection
        try:
            self.mongodb.collection_name = collection_name
            self.mongodb.collection = self.mongodb.db[collection_name]
            yield
        finally:
            self.mongodb.collection_name = original_name
            self.mongodb.collection = original_collection

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join((text or "").strip().split())

    @staticmethod
    def _fact_fingerprint(user_id: str, fact: str) -> str:
        canonical = f"{user_id}:{fact.lower().strip()}"
        return hashlib.sha1(canonical.encode("utf-8")).hexdigest()

    async def store_chat_turn(self, user_id: str, message: str, reply: str):
        """Stores a conversation turn in MongoDB and RAG."""
        message = self._normalize_text(message)
        reply = self._normalize_text(reply)
        turn = {
            "user_id": user_id,
            "message": message,
            "reply": reply,
            "created_at": time.time()
        }

        # 1. Store in MongoDB for precise history
        if self.mongodb:
            with self._use_collection(self.chat_collection):
                self.mongodb.insert_one(turn)

        # 2. Store in RAG for semantic search
        text = f"User: {message}\nAssistant: {reply}"
        await self.rag.ingest(
            record_id=f"chat_{uuid.uuid4().hex}",
            text=text,
            metadata={"type": "chat", "user_id": user_id},
        )

    async def store_fact(self, user_id: str, fact: str):
        """Stores a long-term fact about the user."""
        fact = self._normalize_text(fact)
        if not fact:
            return

        fingerprint = self._fact_fingerprint(user_id, fact)

        # 1. Store in MongoDB
        if self.mongodb:
            with self._use_collection(self.fact_collection):
                self.mongodb.insert_one(
                    {
                        "user_id": user_id,
                        "fact": fact,
                        "fingerprint": fingerprint,
                        "created_at": time.time(),
                    }
                )

        # 2. Store in RAG
        await self.rag.ingest(
            record_id=f"fact_{fingerprint}",
            text=fact,
            metadata={
                "type": "fact",
                "user_id": user_id,
                "fingerprint": fingerprint,
            },
        )

    async def get_context(self, query: str, user_id: str, top_k: int = 5) -> str:
        """Retrieves semantic context for a query."""
        top_k = max(1, int(top_k))
        return await self.rag.build_grouped_context(
            query_text=query,
            user_id=user_id,
            facts_top_k=max(1, min(3, top_k)),
            chats_top_k=max(2, top_k),
        )

    def get_recent_history(self, user_id: str, limit: int = 5) -> str:
        """Retrieves recent N turns from MongoDB."""
        if not self.mongodb:
            return "No persistent history available."

        with self._use_collection(self.chat_collection):
            history = self.mongodb.find_many(
                {"user_id": user_id},
                limit=limit,
                sort_by="created_at",
                descending=True,
            )

        if not history:
            return "No recent history found."

        lines = []
        # Reversed to return chronological order.
        for turn in reversed(history):
            message = str(turn.get("message", "")).strip()
            reply = str(turn.get("reply", "")).strip()
            if not message and not reply:
                continue
            lines.append(f"User: {message}\nAssistant: {reply}")
        return "\n---\n".join(lines)
