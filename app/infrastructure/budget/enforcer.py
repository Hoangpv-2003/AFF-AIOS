"""Budget hard-cutoff checks performed before provider-like calls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from app.infrastructure.budget.budget_ledger import BudgetLedger, budget_ledger


@dataclass
class BudgetEnforcer:
    task_limit: int
    user_limit: int
    org_limit: int
    ledger: BudgetLedger = budget_ledger

    def estimate_tokens(self, text: str) -> int:
        normalized = text.strip()
        if not normalized:
            return 1
        return max(1, int(len(normalized) / 4) + 1)

    def preflight(self, task_id: str, user_id: str, org_id: str, tokens: int) -> Tuple[bool, str]:
        usage = self.ledger.get_usage(task_id=task_id, user_id=user_id, org_id=org_id)
        projected_task = usage.task_tokens + tokens
        projected_user = usage.user_tokens + tokens
        projected_org = usage.org_tokens + tokens

        if projected_task > self.task_limit:
            return False, "BUDGET_EXCEEDED"
        if projected_user > self.user_limit:
            return False, "BUDGET_EXCEEDED"
        if projected_org > self.org_limit:
            return False, "BUDGET_EXCEEDED"

        self.ledger.consume(task_id=task_id, user_id=user_id, org_id=org_id, tokens=tokens)
        return True, "ACCEPTED"
