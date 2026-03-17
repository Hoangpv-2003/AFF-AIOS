"""In-memory budget usage ledger with rolling window reset support."""

from __future__ import annotations

from dataclasses import dataclass
from time import time
from typing import Dict


@dataclass
class UsageWindow:
    task_tokens: int = 0
    user_tokens: int = 0
    org_tokens: int = 0


class BudgetLedger:
    def __init__(self, window_seconds: int = 3600) -> None:
        self.window_seconds = window_seconds
        self._window_started_at = time()
        self._task_usage: Dict[str, int] = {}
        self._user_usage: Dict[str, int] = {}
        self._org_usage: Dict[str, int] = {}

    def _reset_window_if_needed(self) -> None:
        if time() - self._window_started_at < self.window_seconds:
            return
        self.clear()

    def get_usage(self, task_id: str, user_id: str, org_id: str) -> UsageWindow:
        self._reset_window_if_needed()
        return UsageWindow(
            task_tokens=self._task_usage.get(task_id, 0),
            user_tokens=self._user_usage.get(user_id, 0),
            org_tokens=self._org_usage.get(org_id, 0),
        )

    def consume(self, task_id: str, user_id: str, org_id: str, tokens: int) -> None:
        self._reset_window_if_needed()
        self._task_usage[task_id] = self._task_usage.get(task_id, 0) + tokens
        self._user_usage[user_id] = self._user_usage.get(user_id, 0) + tokens
        self._org_usage[org_id] = self._org_usage.get(org_id, 0) + tokens

    def clear(self) -> None:
        self._window_started_at = time()
        self._task_usage = {}
        self._user_usage = {}
        self._org_usage = {}


budget_ledger = BudgetLedger()
