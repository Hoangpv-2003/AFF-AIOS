"""Real Redis/RQ queue adapter."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Dict, Optional

import redis

from app.infrastructure.queue.queue_client import QueueJob


class RedisRQRealClient:
    """Queue implementation using real Redis server."""

    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url
        self.client = redis.from_url(redis_url, decode_responses=True)
        self._jobs_prefix = "aaf_job:"
        self._queue_prefix = "aaf_queue:"

    def submit(self, priority: str, payload: Dict[str, str]) -> QueueJob:
        job_id = f"job-{uuid.uuid4().hex[:10]}"
        job = QueueJob(job_id=job_id, priority=priority, payload=payload)
        
        # Store job data in hash
        self.client.hset(
            f"{self._jobs_prefix}{job_id}",
            mapping={
                "id": job_id,
                "priority": priority,
                "status": job.status,
                "payload": json.dumps(payload),
                "created_at": str(job.created_at),
            },
        )
        
        # Add to priority-based list
        self.client.rpush(f"{self._queue_prefix}{priority}", job_id)
        return job

    def cancel(self, job_id: str) -> bool:
        job_key = f"{self._jobs_prefix}{job_id}"
        if not self.client.exists(job_key):
            return False
            
        status = self.client.hget(job_key, "status")
        if status == "cancelled":
            return True
            
        self.client.hset(job_key, "status", "cancelled")
        # In a real RQ, we'd also remove from the list if possible, 
        # but here we'll just mark it as cancelled for the consumer to skip.
        return True

    def get_status(self, job_id: str) -> str:
        status = self.client.hget(f"{self._jobs_prefix}{job_id}", "status")
        return status if status else "missing"

    def queue_depth(self, priority: str) -> int:
        return self.client.llen(f"{self._queue_prefix}{priority}")

    def metrics(self) -> Dict[str, int]:
        return {
            "queued_interactive": self.queue_depth("interactive"),
            "queued_standard": self.queue_depth("standard"),
            "queued_batch": self.queue_depth("batch"),
            "total_jobs": len(self.client.keys(f"{self._jobs_prefix}*")),
        }

    def health(self) -> Dict[str, str]:
        try:
            self.client.ping()
            return {
                "status": "ok",
                "backend": "redis_real",
                "url": self.redis_url.split("@")[-1], # Mask password
            }
        except Exception as e:
            return {"status": "error", "message": str(e), "backend": "redis_real"}
