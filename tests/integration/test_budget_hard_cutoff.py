from app.agents.base_agent import AgentContext
from app.brain.planner import PlannerAgent
from app.infrastructure.budget.budget_ledger import BudgetLedger
from app.infrastructure.budget.enforcer import BudgetEnforcer


def test_budget_hard_cutoff_blocks_before_provider_and_no_usage_growth():
    ledger = BudgetLedger(window_seconds=3600)
    enforcer = BudgetEnforcer(task_limit=8, user_limit=8, org_limit=8, ledger=ledger)
    planner = PlannerAgent(budget_enforcer=enforcer)

    context = AgentContext(
        task_id="task-budget-1",
        trace_id="trace-budget-1",
        prompt="short",
        metadata={"user_id": "user-1", "org_id": "org-1"},
    )

    first = planner.act(context, {"prompt": "build api"})
    assert first.success is True

    before = ledger.get_usage("task-budget-1", "user-1", "org-1")

    second = planner.act(context, {"prompt": "x" * 80})
    assert second.success is False
    assert second.reason_code == "BUDGET_EXCEEDED"

    after = ledger.get_usage("task-budget-1", "user-1", "org-1")
    assert after.task_tokens == before.task_tokens
    assert after.user_tokens == before.user_tokens
    assert after.org_tokens == before.org_tokens
