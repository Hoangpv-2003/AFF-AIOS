"""MongoDB data store adapter."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from pymongo import MongoClient


class MongoDBStore:
    """Document store implementation using MongoDB."""

    def __init__(
        self,
        uri: str,
        db_name: str = "agentic",
        collection_name: str = "messages",
    ) -> None:
        self.uri = uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.client: MongoClient = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def insert_one(self, document: Dict[str, Any]) -> str:
        if "created_at" not in document:
            document["created_at"] = time.time()
        result = self.collection.insert_one(document)
        return str(result.inserted_id)

    def find_many(
        self,
        query: Dict[str, Any],
        limit: int = 100,
        sort_by: str = "created_at",
        descending: bool = True,
    ) -> List[Dict[str, Any]]:
        cursor = self.collection.find(query).limit(limit)
        if sort_by:
            cursor = cursor.sort(sort_by, -1 if descending else 1)
        return list(cursor)

    def delete_many(self, query: Dict[str, Any]) -> int:
        result = self.collection.delete_many(query)
        return result.deleted_count

    def health(self) -> Dict[str, str]:
        try:
            self.client.admin.command("ping")
            return {
                "status": "ok",
                "backend": "mongodb",
                "database": self.db_name,
                "collection": self.collection_name,
            }
        except Exception as e:
            return {"status": "error", "message": str(e), "backend": "mongodb"}
