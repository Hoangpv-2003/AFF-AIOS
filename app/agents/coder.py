"""Coder agent implementation for generating draft artifacts from plan."""

from __future__ import annotations

import json
import time
from typing import Any
from typing import Dict, List, Optional, Tuple

from app.agents.base_agent import AgentContext, AgentResult, BaseAgent
from app.brain.prompt_templates import build_coder_messages
from app.brain.rag import RAGService
from app.infrastructure.budget.enforcer import BudgetEnforcer
from app.schemas.agents import CoderArtifactDraft, PlanDraft


class CoderAgent(BaseAgent):
    name = "coder"

    def __init__(
        self,
        budget_enforcer: BudgetEnforcer | None = None,
        llm_client: Any | None = None,
        rag_service: RAGService | None = None,
    ) -> None:
        self.budget_enforcer = budget_enforcer
        self.llm_client = llm_client
        self.rag_service = rag_service

    def _build_llm_rationale(
        self,
        plan: PlanDraft,
        memory_context: str,
        fallback: str,
    ) -> Tuple[str, bool]:
        if self.llm_client is None or not hasattr(self.llm_client, "generate"):
            return fallback, False

        messages = build_coder_messages(
            plan_json=plan.model_dump_json(),
            memory_context=memory_context,
        )
        system_prompt = messages[0]["content"]
        prompt = messages[1]["content"]

        try:
            generated = str(
                self.llm_client.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                )
            ).strip()
        except Exception:
            return fallback, False

        if not generated:
            return fallback, False

        try:
            payload = json.loads(generated)
            rationale = str(payload.get("rationale", "")).strip()
            if rationale:
                return rationale, True
        except Exception:
            pass
        return generated, True

    def generate_artifacts(
        self,
        plan: PlanDraft,
        memory_hits: Optional[List[Dict[str, str]]] = None,
        memory_context: str = "",
    ) -> Tuple[CoderArtifactDraft, bool]:
        slug = plan.objective.lower().replace(" ", "_")
        files = [
            f"skills/dynamic/{slug}.py",
            f"tests/generated/test_{slug}.py",
        ]
        fallback_rationale = (
            f"Generated from plan with {len(plan.steps)} step(s)."
            f" memory_hits={len(memory_hits or [])}"
        )
        rationale, llm_used = self._build_llm_rationale(
            plan=plan,
            memory_context=memory_context,
            fallback=fallback_rationale,
        )
        return CoderArtifactDraft(files=files, rationale=rationale), llm_used

    def act(
        self,
        context: AgentContext,
        inputs: Dict[str, object],
    ) -> AgentResult:
        plan_data = inputs.get("plan")
        if not isinstance(plan_data, dict):
            return AgentResult(success=False, reason_code="VALIDATION_FAILED")

        plan = PlanDraft(**plan_data)
        memory_context = ""
        if self.rag_service is not None:
            memory_context = self.rag_service.build_context(
                query_text=plan.objective,
                top_k=3,
            )

        if self.budget_enforcer is not None:
            user_id = str(context.metadata.get("user_id", "system"))
            org_id = str(context.metadata.get("org_id", "default"))
            step_text = " ".join(plan.steps)
            plan_text = (
                f"{plan.objective} {step_text} {memory_context}".strip()
            )
            tokens = self.budget_enforcer.estimate_tokens(plan_text)
            allowed, reason = self.budget_enforcer.preflight(
                task_id=context.task_id,
                user_id=user_id,
                org_id=org_id,
                tokens=tokens,
            )
            if not allowed:
                return AgentResult(success=False, reason_code=reason)

        artifacts, llm_used = self.generate_artifacts(
            plan=plan,
            memory_hits=inputs.get("memory_hits"),
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
                record_id=f"code-{context.task_id}-{int(time.time() * 1000)}",
                text=(
                    f"objective={plan.objective}\n"
                    f"rationale={artifacts.rationale}"
                ),
                metadata={"type": "code", "task_id": context.task_id},
            )
        return AgentResult(
            success=True,
            payload={
                "artifacts": artifacts.model_dump(),
                "debug": {
                    "llm_used": llm_used,
                    "llm_debug": llm_debug,
                    "memory_context": memory_context,
                },
            },
        )
