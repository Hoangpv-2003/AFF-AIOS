from __future__ import annotations

import json

from app.agents.base_agent import AgentContext
from app.brain.planner import PlannerAgent


class JsonLLM:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> str:
        del prompt, system_prompt, model
        return json.dumps(self.payload, ensure_ascii=False)


def _ctx(task_id: str, prompt: str) -> AgentContext:
    return AgentContext(task_id=task_id, trace_id=f"trace-{task_id}", prompt=prompt)


def test_planner_filters_disallowed_delivery_and_schedule_skills():
    llm_payload = {
        "task_summary": "Tao bao cao doanh thu 2025",
        "skills_to_create": [
            {
                "skill_name": "collect-revenue-data",
                "skill_kind": "retrieve",
                "skill_purpose": "Collect source records",
                "coder_notes": "URL: https://api.tavily.com/search. POST.",
            },
            {
                "skill_name": "notify-finance-team",
                "skill_kind": "deliver",
                "skill_purpose": "Notify downstream consumer",
                "coder_notes": "Use SMTP SSL.",
            },
            {
                "skill_name": "daily-report-job",
                "skill_kind": "schedule",
                "skill_purpose": "Register periodic run",
                "coder_notes": "Create cron job registration.",
            },
        ],
        "confidence": 0.9,
    }
    planner = PlannerAgent(llm_client=JsonLLM(llm_payload))

    intent = {
        "action_type": "generate",
        "entities": {
            "topic": "bao cao doanh thu viettel 2025",
            "recipient": "",
            "schedule_time": "",
        },
    }
    result = planner.act(
        _ctx("planner-guard-1", "tao bao cao doanh thu viettel 2025"),
        {"intent_json": intent},
    )

    assert result.success is True
    plan = (result.payload or {}).get("plan", {})
    skill_names = [
        str(item.get("skill_name", ""))
        for item in plan.get("skills_to_create", [])
        if isinstance(item, dict)
    ]

    assert "collect-revenue-data" in skill_names
    assert "notify-finance-team" not in skill_names
    assert "daily-report-job" not in skill_names


def test_planner_keeps_delivery_skills_when_intent_allows_it():
    llm_payload = {
        "task_summary": "Tao va gui bao cao doanh thu 2025",
        "skills_to_create": [
            {
                "skill_name": "collect-revenue-data",
                "skill_kind": "retrieve",
                "skill_purpose": "Collect source records",
                "coder_notes": "URL: https://api.tavily.com/search. POST.",
            },
            {
                "skill_name": "notify-finance-team",
                "skill_kind": "deliver",
                "skill_purpose": "Notify downstream consumer",
                "coder_notes": "Use SMTP SSL.",
            },
        ],
        "confidence": 0.9,
    }
    planner = PlannerAgent(llm_client=JsonLLM(llm_payload))

    intent = {
        "action_type": "pipeline",
        "entities": {
            "topic": "bao cao doanh thu viettel 2025",
            "recipient": "team@example.com",
        },
    }
    result = planner.act(
        _ctx("planner-guard-2", "tao va gui bao cao doanh thu viettel 2025"),
        {"intent_json": intent},
    )

    assert result.success is True
    plan = (result.payload or {}).get("plan", {})
    skill_names = [
        str(item.get("skill_name", ""))
        for item in plan.get("skills_to_create", [])
        if isinstance(item, dict)
    ]

    assert "collect-revenue-data" in skill_names
    assert "notify-finance-team" in skill_names
