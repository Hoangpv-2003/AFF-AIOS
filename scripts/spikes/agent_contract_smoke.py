"""Agent contract smoke runner for planner/coder/reviewer shape stability."""

import json

from app.agents.base_agent import AgentContext
from app.agents.coder import CoderAgent
from app.agents.reviewer import ReviewerAgent
from app.brain.planner import PlannerAgent
from app.schemas.agents import PlanDraft, ReviewStatus, ReviewVerdictDraft


def run_spike(task_samples=None):
    samples = task_samples or [
        "Create auth endpoint. Add tests.",
        "Implement queue retry policy.",
        "Build reconciliation report.",
    ]

    planner = PlannerAgent()
    coder = CoderAgent()
    reviewer = ReviewerAgent()

    plan_ok = 0
    verdict_ok = 0

    for index, prompt in enumerate(samples):
        context = AgentContext(
            task_id=f"spike-agent-{index}",
            trace_id=f"trace-spike-agent-{index}",
            prompt=prompt,
        )

        plan_result = planner.act(context, {"prompt": prompt})
        if not plan_result.success:
            continue

        plan_payload = (plan_result.payload or {}).get("plan", {})
        try:
            plan = PlanDraft(**plan_payload)
            plan_ok += 1
        except Exception:
            continue

        artifacts_result = coder.act(context, {"plan": plan.model_dump(), "memory_hits": []})
        if not artifacts_result.success:
            continue

        verdict_result = reviewer.act(
            context,
            {"artifacts": (artifacts_result.payload or {}).get("artifacts", {})},
        )
        verdict_payload = (verdict_result.payload or {}).get("verdict", {}) if verdict_result.success else {}
        try:
            verdict = ReviewVerdictDraft(**verdict_payload)
            if verdict.status in {ReviewStatus.pass_, ReviewStatus.warn, ReviewStatus.fail}:
                verdict_ok += 1
        except Exception:
            continue

    total = float(len(samples)) if samples else 1.0
    return {
        "scenario": "agent_contract",
        "samples": len(samples),
        "plan_schema_pass_rate": round(plan_ok / total, 4),
        "verdict_parse_rate": round(verdict_ok / total, 4),
        "status": "ok",
    }


if __name__ == "__main__":
    print(json.dumps(run_spike(), indent=2))
