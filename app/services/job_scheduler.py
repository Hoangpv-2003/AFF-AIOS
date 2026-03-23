"""Centralized Job Scheduler – Singleton.

Quản lý tất cả scheduled jobs với:  
- Deduplication theo job_id  
- stop_event riêng mỗi job  
- Persistence vào MongoDB (khôi phục sau restart)  
"""
from __future__ import annotations

import importlib.util
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("aaf.scheduler")


@dataclass
class ScheduledJob:
    job_id: str
    skill_name: str
    time_str: str          # "HH:MM" 24h
    parameters: Dict[str, Any]
    recurrence: str = "daily"  # daily | monthly
    day_of_month: Optional[int] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "active"


class JobScheduler:
    """Singleton scheduler – một instance duy nhất trong toàn bộ process."""

    _instance: Optional["JobScheduler"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._jobs: Dict[str, ScheduledJob] = {}          # job_id -> job
        self._stop_events: Dict[str, threading.Event] = {}  # job_id -> event
        self._db = None  # lazy MongoDB client

    # ------------------------------------------------------------------ #
    # Singleton
    # ------------------------------------------------------------------ #
    @classmethod
    def get_instance(cls) -> "JobScheduler":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def add_job(
        self,
        skill_name: str,
        time_str: str,
        parameters: Optional[Dict[str, Any]] = None,
        job_id: Optional[str] = None,
        recurrence: str = "daily",
        day_of_month: Optional[int] = None,
    ) -> str:
        """Thêm job mới. Bỏ qua nếu job_id đã tồn tại (deduplication)."""
        if job_id is None:
            suffix = time_str.replace(':', '')
            if recurrence == "monthly":
                day_suffix = day_of_month if day_of_month is not None else 1
                suffix = f"m{day_suffix:02d}-{suffix}"
            job_id = f"{skill_name}-{suffix}"

        recurrence = (recurrence or "daily").strip().lower()
        if recurrence not in {"daily", "monthly"}:
            recurrence = "daily"
        if recurrence == "monthly":
            if day_of_month is None:
                day_of_month = 1
            day_of_month = max(1, min(28, int(day_of_month)))

        with self._lock:
            if job_id in self._jobs:
                logger.info("Job %s already registered – skipping.", job_id)
                return job_id

            job = ScheduledJob(
                job_id=job_id,
                skill_name=skill_name,
                time_str=time_str,
                parameters=parameters or {},
                recurrence=recurrence,
                day_of_month=day_of_month,
            )
            self._jobs[job_id] = job
            self._persist(job)
            self._spawn_thread(job)

        logger.info("Job %s registered: %s at %s", job_id, skill_name, time_str)
        return job_id

    def cancel_job(self, job_id: str) -> bool:
        """Dừng và xóa job."""
        with self._lock:
            if job_id not in self._jobs:
                return False
            event = self._stop_events.pop(job_id, None)
            if event:
                event.set()
            self._jobs.pop(job_id, None)
            self._remove_from_db(job_id)
        logger.info("Job %s cancelled.", job_id)
        return True

    def list_jobs(self) -> list:
        with self._lock:
            return [
                {
                    "job_id": j.job_id,
                    "skill_name": j.skill_name,
                    "time_str": j.time_str,
                    "recurrence": j.recurrence,
                    "day_of_month": j.day_of_month,
                    "status": j.status,
                    "created_at": j.created_at,
                }
                for j in self._jobs.values()
            ]

    def stop_all(self) -> None:
        with self._lock:
            for event in self._stop_events.values():
                event.set()
            self._stop_events.clear()
        logger.info("All scheduler jobs stopped.")

    # ------------------------------------------------------------------ #
    # Persistence / Recovery
    # ------------------------------------------------------------------ #
    def reload_from_db(self) -> None:
        """Khôi phục tất cả active jobs từ MongoDB sau khi server restart."""
        try:
            collection = self._get_collection()
            if collection is None:
                return
            for doc in collection.find({"status": "active"}):
                job_id = doc.get("job_id")
                if job_id and job_id not in self._jobs:
                    job = ScheduledJob(
                        job_id=job_id,
                        skill_name=doc["skill_name"],
                        time_str=doc["time_str"],
                        parameters=doc.get("parameters", {}),
                        recurrence=str(doc.get("recurrence") or "daily"),
                        day_of_month=doc.get("day_of_month"),
                        created_at=doc.get("created_at", datetime.utcnow().isoformat()),
                        status="active",
                    )
                    self._jobs[job_id] = job
                    self._spawn_thread(job)
            logger.info("Scheduler reloaded %d jobs from MongoDB.", len(self._jobs))
        except Exception as exc:
            logger.warning("Could not reload jobs from MongoDB: %s", exc)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _spawn_thread(self, job: ScheduledJob) -> None:
        stop_event = threading.Event()
        self._stop_events[job.job_id] = stop_event

        def _loop() -> None:
            logger.info("Thread for job %s started.", job.job_id)
            while not stop_event.is_set():
                now = datetime.now()
                should_run = now.strftime("%H:%M") == job.time_str
                if should_run and job.recurrence == "monthly":
                    target_day = job.day_of_month or 1
                    should_run = now.day == target_day

                if should_run:
                    try:
                        self._run_skill(job.skill_name, job.parameters)
                    except Exception as exc:
                        logger.error("Error running skill %s: %s", job.skill_name, exc)
                    # Sleep 61s to avoid double-firing within same minute
                    stop_event.wait(61)
                else:
                    stop_event.wait(30)

        t = threading.Thread(target=_loop, daemon=True, name=f"job-{job.job_id}")
        t.start()

    def _run_skill(self, skill_name: str, parameters: Dict[str, Any]) -> None:
        root = Path(__file__).resolve().parent.parent.parent

        # Tìm skill_impl.py theo cả hai thư mục static/dynamic
        for folder in ("static", "dynamic"):
            impl_path = root / "skills" / folder / skill_name / "scripts" / "skill_impl.py"
            if impl_path.exists():
                break
            # Fallback về flat file trong app/skills/
            impl_path = root / "app" / "skills" / folder / f"{skill_name}.py"
            if impl_path.exists():
                break
        else:
            logger.error("Skill not found: %s", skill_name)
            return

        module_name = f"aaf_sched_{uuid.uuid4().hex[:8]}"
        spec = importlib.util.spec_from_file_location(module_name, impl_path)
        if spec is None or spec.loader is None:
            return
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        run_fn = getattr(module, "run", None)
        if callable(run_fn):
            result = run_fn(input_data=parameters)
            logger.info("Skill %s result: %s", skill_name, result.get("status"))

    def _persist(self, job: ScheduledJob) -> None:
        try:
            col = self._get_collection()
            if col is None:
                return
            col.update_one(
                {"job_id": job.job_id},
                {"$set": {
                    "job_id": job.job_id,
                    "skill_name": job.skill_name,
                    "time_str": job.time_str,
                    "parameters": job.parameters,
                    "recurrence": job.recurrence,
                    "day_of_month": job.day_of_month,
                    "created_at": job.created_at,
                    "status": "active",
                }},
                upsert=True,
            )
        except Exception as exc:
            logger.warning("Could not persist job %s: %s", job.job_id, exc)

    def _remove_from_db(self, job_id: str) -> None:
        try:
            col = self._get_collection()
            if col is not None:
                col.update_one({"job_id": job_id}, {"$set": {"status": "cancelled"}})
        except Exception as exc:
            logger.warning("Could not remove job %s from DB: %s", job_id, exc)

    def _get_collection(self):
        try:
            if self._db is None:
                import os
                import pymongo
                mongo_uri = os.getenv("MONGODB_URI")
                mongo_db = os.getenv("MONGODB_DB", "agentic")
                if not mongo_uri:
                    return None
                client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
                self._db = client[mongo_db]
            return self._db["scheduled_jobs"]
        except Exception:
            return None
