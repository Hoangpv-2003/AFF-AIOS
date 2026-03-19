from __future__ import annotations
import time
from typing import Any, Dict, List, Optional
from app.brain.rag import RAGService
from app.infrastructure.database.mongodb_store import MongoDBStore

class MemoryManager:
    """Manages short-term (chat) and long-term (facts) memory using MongoDB and RAG (Qdrant)."""
    
    def __init__(self, rag_service: RAGService, mongodb: Optional[MongoDBStore] = None):
        self.rag = rag_service
        self.mongodb = mongodb
        self.chat_collection = "chat_history"
        self.fact_collection = "facts"

    def store_chat_turn(self, user_id: str, message: str, reply: str):
        """Stores a conversation turn in MongoDB and RAG."""
        turn = {
            "user_id": user_id,
            "message": message,
            "reply": reply,
            "created_at": time.time()
        }
        
        # 1. Store in MongoDB for precise history
        if self.mongodb:
            # Switch to chat collection
            original_coll = self.mongodb.collection_name
            self.mongodb.collection_name = self.chat_collection
            self.mongodb.collection = self.mongodb.db[self.chat_collection]
            self.mongodb.insert_one(turn)
            self.mongodb.collection_name = original_coll # restore
            
        # 2. Store in RAG for semantic search
        text = f"User: {message}\nAssistant: {reply}"
        self.rag.ingest(record_id=f"chat_{int(time.time()*1000)}", text=text, metadata={"type": "chat", "user_id": user_id})

    def store_fact(self, user_id: str, fact: str):
        """Stores a long-term fact about the user."""
        if not fact: return
        
        # 1. Store in MongoDB
        if self.mongodb:
            original_coll = self.mongodb.collection_name
            self.mongodb.collection_name = self.fact_collection
            self.mongodb.collection = self.mongodb.db[self.fact_collection]
            self.mongodb.insert_one({"user_id": user_id, "fact": fact, "created_at": time.time()})
            self.mongodb.collection_name = original_coll 
            
        # 2. Store in RAG
        self.rag.ingest(record_id=f"fact_{int(time.time()*1000)}", text=fact, metadata={"type": "fact", "user_id": user_id})

    def get_context(self, query: str, user_id: str, top_k: int = 5) -> str:
        """Retrieves semantic context for a query."""
        results = self.rag.retrieve(query, top_k=top_k, filters={"user_id": user_id})
        if not results:
            return ""
        
        facts = [r.record.text for r in results if r.record.metadata.get("type") == "fact"]
        chats = [r.record.text for r in results if r.record.metadata.get("type") == "chat"]
        
        context = "## Long-term Facts\n" + ("\n".join(facts) if facts else "No facts found.")
        context += "\n\n## Relevant Chat History\n" + ("\n".join(chats) if chats else "No relevant history.")
        return context

    def get_recent_history(self, user_id: str, limit: int = 5) -> str:
        """Retrieves recent N turns from MongoDB."""
        if not self.mongodb: return "No persistent history available."
        
        original_coll = self.mongodb.collection_name
        self.mongodb.collection_name = self.chat_collection
        self.mongodb.collection = self.mongodb.db[self.chat_collection]
        history = self.mongodb.find_many({"user_id": user_id}, limit=limit, sort_by="created_at", descending=True)
        self.mongodb.collection_name = original_coll
        
        if not history: return "No recent history found."
        
        lines = []
        # Reversed to be chronological
        for turn in reversed(history):
            lines.append(f"User: {turn['message']}\nAssistant: {turn['reply']}")
        return "\n---\n".join(lines)
