"""Planner agent implementation for NL -> plan decomposition."""

from __future__ import annotations

import json
import time
from typing import Any
from typing import Dict, List, Tuple

from app.agents.base_agent import AgentContext, AgentResult, BaseAgent
from app.brain.prompt_templates import build_planner_messages
from app.brain.rag import RAGService
from app.brain.reasoning import validate_non_empty
from app.infrastructure.budget.enforcer import BudgetEnforcer
from app.schemas.agents import PlanDraft


class PlannerAgent(BaseAgent):
    name = "planner"

    def __init__(
        self,
        budget_enforcer: BudgetEnforcer | None = None,
        llm_client: Any | None = None,
        rag_service: RAGService | None = None,
    ) -> None:
        self.budget_enforcer = budget_enforcer
        self.llm_client = llm_client
        self.rag_service = rag_service

    def create_plan(self, task_input: str) -> PlanDraft:
        validate_non_empty(task_input, "task_input")
        raw_steps = [
            step.strip()
            for step in task_input.split(".")
            if step.strip()
        ]
        steps: List[str] = (
            raw_steps if raw_steps else ["analyze task", "produce output"]
        )
        confidence = 0.8 if len(steps) >= 2 else 0.6
        return PlanDraft(
            objective=task_input.strip(),
            steps=steps,
            confidence=confidence,
        )

    def _create_plan_with_llm(
        self,
        task_input: str,
        memory_context: str = "",
    ) -> Tuple[PlanDraft, bool, str]:
        if self.llm_client is None or not hasattr(self.llm_client, "generate"):
            return self.create_plan(task_input), False, ""

        messages = build_planner_messages(
            task_input=task_input,
            memory_context=memory_context,
        )
        system_prompt = messages[0]["content"]
        llm_prompt = messages[1]["content"]

        try:
            response = str(
                self.llm_client.generate(
                    prompt=llm_prompt,
                    system_prompt=system_prompt,
                )
            ).strip()
        except Exception:
            return self.create_plan(task_input), False, ""

        candidate_steps: List[str] = []
        confidence = 0.85
        arch_decisions = None
        planner_notes = ""
        try:
            parsed = json.loads(response)
            parsed_steps = parsed.get("steps") or []
            for item in parsed_steps:
                if isinstance(item, dict):
                    step_name = str(
                        item.get("name") or item.get("description") or ""
                    ).strip()
                    if step_name:
                        candidate_steps.append(step_name)
                elif isinstance(item, str) and item.strip():
                    candidate_steps.append(item.strip())
            confidence = float(parsed.get("confidence", 0.85))
            arch_decisions = parsed.get("architectural_decisions")
            planner_notes = str(parsed.get("planner_notes") or "").strip()
        except Exception:
            candidate_steps = [
                line.strip("- *\t ")
                for line in response.splitlines()
                if line.strip()
            ]

        steps = (
            candidate_steps[:8]
            if candidate_steps
            else ["analyze task", "produce output"]
        )
        confidence = confidence if candidate_steps else 0.6
        plan = PlanDraft(
            objective=task_input.strip(),
            steps=steps,
            confidence=confidence,
            architectural_decisions=arch_decisions,
            planner_notes=planner_notes,
        )
        return plan, bool(candidate_steps), response

    def act(
        self,
        context: AgentContext,
        inputs: Dict[str, str],
    ) -> AgentResult:
        prompt = inputs.get("prompt", context.prompt)
        memory_context = ""
        if self.rag_service is not None:
            memory_context = self.rag_service.build_context(
                query_text=prompt,
                top_k=3,
            )
        if self.budget_enforcer is not None:
            user_id = str(context.metadata.get("user_id", "system"))
            org_id = str(context.metadata.get("org_id", "default"))
            tokens = self.budget_enforcer.estimate_tokens(
                f"{prompt}\n{memory_context}"
            )
            allowed, reason = self.budget_enforcer.preflight(
                task_id=context.task_id,
                user_id=user_id,
                org_id=org_id,
                tokens=tokens,
            )
            if not allowed:
                return AgentResult(success=False, reason_code=reason)

        # Incorporate conversation history if available
        if context.history_summary:
            prompt = (
                f"## Lich su cuoc chat\n{context.history_summary}\n\n"
                f"## Yeu cau hien tai\n{prompt}"
            )

        plan, llm_used, llm_output = self._create_plan_with_llm(
            prompt,
            memory_context=memory_context,
        )
        llm_debug = {}
        if (
            self.llm_client is not None
            and hasattr(self.llm_client, "get_last_debug")
        ):
            try:
                llm_debug = dict(self.llm_client.get_last_debug())
            except Exception:
                llm_debug = {}
        if self.rag_service is not None:
            self.rag_service.ingest(
                record_id=f"plan-{context.task_id}-{int(time.time() * 1000)}",
                text=f"task={prompt}\nsteps={' | '.join(plan.steps)}",
                metadata={"type": "plan", "task_id": context.task_id},
            )
        return AgentResult(
            success=True,
            payload={
                "plan": plan.model_dump(),
                "debug": {
                    "llm_used": llm_used,
                    "llm_output": llm_output,
                    "llm_debug": llm_debug,
                    "memory_context": memory_context,
                },
            },
        )
