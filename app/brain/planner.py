"""Planner agent implementation for NL -> plan decomposition."""

from __future__ import annotations

import json
import time
from typing import Any
from typing import Dict, List, Tuple

from app.agents.base_agent import AgentContext, AgentResult, BaseAgent
from app.brain.prompt_templates import build_planner_messages, build_runtime_context
from app.brain.rag import RAGService
from app.brain.reasoning import validate_non_empty
from app.infrastructure.budget.enforcer import BudgetEnforcer
from app.schemas.agents import PlanDraft, SkillSpec


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
        """Fallback: create a single SkillSpec for the whole task."""
        validate_non_empty(task_input, "task_input")
        return PlanDraft(
            task_summary=task_input.strip(),
            skills_to_create=[
                SkillSpec(
                    skill_name="fallback_skill",
                    skill_purpose=task_input.strip(),
                    coder_notes=f"Implement: {task_input.strip()}",
                )
            ],
            confidence=0.5,
        )

    def _create_plan_with_llm(
        self,
        intent_json: str,
        runtime_context: str = "",
        memory_context: str = "",
        validator_feedback: str = "",
    ) -> Tuple[PlanDraft, bool, str]:
        if self.llm_client is None or not hasattr(self.llm_client, "generate"):
            return self.create_plan(intent_json), False, ""

        messages = build_planner_messages(
            intent_json=intent_json,
            runtime_context=runtime_context,
            memory_context=memory_context,
            validator_feedback=validator_feedback,
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
            return self.create_plan(intent_json), False, ""

        skills: List[SkillSpec] = []
        confidence = 0.85
        task_summary = ""
        
        try:
            parsed = json.loads(response)
            task_summary = parsed.get("task_summary") or ""
            raw_skills = parsed.get("skills_to_create") or []
            for item in raw_skills:
                if isinstance(item, dict) and "skill_name" in item:
                    skills.append(SkillSpec(**item))
            confidence = float(parsed.get("confidence", 0.85))
        except Exception:
            # Fallback parsing if JSON was malformed but partially usable
            task_summary = intent_json[:100]
            skills = [
                SkillSpec(
                    skill_name="custom_skill",
                    skill_purpose=intent_json,
                    coder_notes=response
                )
            ]

        if not skills:
            return self.create_plan(intent_json), False, response

        plan = PlanDraft(
            task_summary=task_summary or intent_json,
            skills_to_create=skills,
            confidence=confidence,
        )
        return plan, True, response

    def act(
        self,
        context: AgentContext,
        inputs: Dict[str, Any],
    ) -> AgentResult:
        # Lỗi 6: Prioritize intent_json over prompt
        intent_json = inputs.get("intent_json", "") or inputs.get("prompt", context.prompt)
        memory_context = ""
        if self.rag_service is not None:
            memory_context = self.rag_service.build_context(
                query_text=str(intent_json),
                top_k=3,
            )
            
        # Lỗi 7: Build runtime_context
        runtime_context = inputs.get("runtime_context", "")
        if not runtime_context and context.metadata.get("current_datetime"):
            runtime_context = build_runtime_context(
                history=inputs.get("history", [])
            )
            # Standard build_runtime_context uses datetime.now() 
            # but usually we want to respect the context metadata if provided.
            # For this task, we follow the user's advice to use build_runtime_context.

        if self.budget_enforcer is not None:
            user_id = str(context.metadata.get("user_id", "system"))
            org_id = str(context.metadata.get("org_id", "default"))
            tokens = self.budget_enforcer.estimate_tokens(
                f"{intent_json}\n{memory_context}"
            )
            allowed, reason = self.budget_enforcer.preflight(
                task_id=context.task_id,
                user_id=user_id,
                org_id=org_id,
                tokens=tokens,
            )
            if not allowed:
                return AgentResult(success=False, reason_code=reason)

        plan, llm_used, llm_output = self._create_plan_with_llm(
            str(intent_json),
            runtime_context=runtime_context,
            memory_context=memory_context,
            validator_feedback=inputs.get("validator_feedback", "")
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
        
        # Lỗi 8: RAG ingest
        if self.rag_service is not None:
            self.rag_service.ingest(
                record_id=f"plan-{context.task_id}-{int(time.time() * 1000)}",
                text=f"task_summary={plan.task_summary}\nskills={' | '.join([s.skill_name for s in plan.skills_to_create])}",
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
