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
from app.schemas.agents import PlanDraft, SkillKind, SkillSpec


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
        planning_mode: str = "standard",
    ) -> Tuple[PlanDraft, bool, str, Dict[str, Any]]:
        if self.llm_client is None or not hasattr(self.llm_client, "generate"):
            return self.create_plan(intent_json), False, "", {}

        messages = build_planner_messages(
            intent_json=intent_json,
            runtime_context=runtime_context,
            memory_context=memory_context,
            validator_feedback=validator_feedback,
            planning_mode=planning_mode,
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
            return self.create_plan(intent_json), False, "", {}

        skills: List[SkillSpec] = []
        confidence = 0.85
        task_summary = ""
        extended_fields: Dict[str, Any] = {}
        parsed_ok = False
        
        try:
            parsed = json.loads(response)
            parsed_ok = isinstance(parsed, dict)
            task_summary = parsed.get("task_summary") or ""
            raw_skills = parsed.get("skills_to_create") or []
            for item in raw_skills:
                if isinstance(item, dict) and "skill_name" in item:
                    spec = SkillSpec(**item)
                    spec.skill_kind = self._normalize_skill_kind(item, spec)
                    skills.append(spec)
            confidence = float(parsed.get("confidence", 0.85))

            for key in (
                "success_criteria",
                "phases",
                "resources",
                "risks",
                "reasoning",
                "assumptions",
                "open_questions",
            ):
                if key in parsed:
                    extended_fields[key] = parsed.get(key)
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

        if not skills and not parsed_ok:
            return self.create_plan(intent_json), False, response, {}

        plan = PlanDraft(
            task_summary=task_summary or intent_json,
            skills_to_create=skills,
            confidence=confidence,
        )
        return plan, True, response, extended_fields

    @staticmethod
    def _extract_intent_object(intent_json: Any) -> Dict[str, Any]:
        if isinstance(intent_json, dict):
            return intent_json
        if isinstance(intent_json, str):
            text = intent_json.strip()
            if text.startswith("{") and text.endswith("}"):
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict):
                        return parsed
                except Exception:
                    return {}
        return {}

    @staticmethod
    def _normalize_skill_kind(raw_item: Dict[str, Any], skill: SkillSpec) -> SkillKind:
        kind_raw = str(raw_item.get("skill_kind") or skill.skill_kind.value).strip().lower()
        if kind_raw in {kind.value for kind in SkillKind}:
            return SkillKind(kind_raw)

        input_keys = raw_item.get("input_keys")
        if not isinstance(input_keys, list):
            input_keys = list(skill.input_keys)
        normalized_keys = {str(key).strip().lower() for key in input_keys}

        if "recipient" in normalized_keys:
            return SkillKind.deliver
        if "schedule_time" in normalized_keys or "cron" in normalized_keys:
            return SkillKind.schedule
        return SkillKind.generate

    @staticmethod
    def _allowed_skill_kinds(intent: Dict[str, Any]) -> set[SkillKind]:
        allowed = {
            SkillKind.retrieve,
            SkillKind.generate,
            SkillKind.analyse,
            SkillKind.mutate,
        }

        action = str(intent.get("action_type", "")).strip().lower()
        if action in {SkillKind.deliver.value, SkillKind.schedule.value}:
            allowed.add(SkillKind(action))

        if action == "pipeline":
            sub_actions = intent.get("sub_actions")
            if isinstance(sub_actions, list):
                for sub in sub_actions:
                    sub_name = str(sub).strip().lower()
                    if sub_name in {kind.value for kind in SkillKind}:
                        allowed.add(SkillKind(sub_name))

        entities = intent.get("entities")
        if isinstance(entities, dict):
            if str(entities.get("recipient", "")).strip():
                allowed.add(SkillKind.deliver)
            if str(entities.get("schedule_time", "")).strip():
                allowed.add(SkillKind.schedule)

        return allowed

    def _enforce_intent_alignment(self, plan: PlanDraft, intent_json: Any) -> PlanDraft:
        intent = self._extract_intent_object(intent_json)
        if not intent:
            return plan

        allowed = self._allowed_skill_kinds(intent)
        filtered = [
            skill
            for skill in plan.skills_to_create
            if skill.skill_kind in allowed
        ]
        if filtered:
            plan.skills_to_create = filtered
        return plan

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

        planning_mode = str(inputs.get("planning_mode", "standard") or "standard").strip().lower()
        if planning_mode not in {"standard", "tot", "multi_persona"}:
            planning_mode = "standard"

        plan, llm_used, llm_output, extended_fields = self._create_plan_with_llm(
            str(intent_json),
            runtime_context=runtime_context,
            memory_context=memory_context,
            validator_feedback=inputs.get("validator_feedback", ""),
            planning_mode=planning_mode,
        )
        plan = self._enforce_intent_alignment(plan, intent_json)
        
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
                text=(
                    f"task={plan.task_summary}\n"
                    f"objective={plan.task_summary}\n"
                    f"skills={' | '.join([s.skill_name for s in plan.skills_to_create])}"
                ),
                metadata={"type": "plan", "task_id": context.task_id},
            )

        plan_payload = plan.model_dump()
        plan_payload["objective"] = plan.task_summary
        steps: List[str] = []
        if llm_output:
            if llm_output.strip().startswith("{"):
                try:
                    parsed = json.loads(llm_output)
                    raw_steps = parsed.get("steps") if isinstance(parsed, dict) else []
                    if isinstance(raw_steps, list):
                        steps = [str(item).strip() for item in raw_steps if str(item).strip()]
                except Exception:
                    steps = []
            else:
                steps = [
                    line.strip().lstrip("-* ")
                    for line in llm_output.splitlines()
                    if line.strip()
                ]
        if not steps:
            steps = [s.coder_notes for s in plan.skills_to_create if s.coder_notes]
        plan_payload["steps"] = steps
        plan_payload["planning_mode"] = planning_mode
        for key, value in extended_fields.items():
            plan_payload[key] = value
            
        return AgentResult(
            success=True,
            payload={
                "plan": plan_payload,
                "debug": {
                    "llm_used": llm_used,
                    "llm_output": llm_output,
                    "llm_debug": llm_debug,
                    "memory_context": memory_context,
                },
            },
        )
