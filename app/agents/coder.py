"""Coder agent implementation for generating draft artifacts from plan."""

from __future__ import annotations

import json
import time
from typing import Any
from typing import Dict, List, Optional, Tuple

import ast
from app.agents.base_agent import AgentContext, AgentResult, BaseAgent
from app.agents.reviewer import ReviewerAgent
from app.brain.prompt_templates import (
    build_coder_messages, 
    build_runtime_context, 
    build_coder_review_messages,
    CODE_GENERATION_TPL
)
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
        reviewer: ReviewerAgent | None = None,
    ) -> None:
        self.budget_enforcer = budget_enforcer
        self.llm_client = llm_client
        self.rag_service = rag_service
        self.reviewer = reviewer or ReviewerAgent(llm_client=llm_client)

    def _build_llm_rationale(
        self,
        plan: PlanDraft,
        skill_name: str,
        memory_context: str,
        runtime_context: str = "",
        patch_mode: str = "create_new",
        fallback: str = "",
    ) -> Tuple[str, bool]:
        if self.llm_client is None or not hasattr(self.llm_client, "generate"):
            return fallback, False

        messages = build_coder_messages(
            plan_json=plan.model_dump_json(),
            skill_name=skill_name,
            memory_context=memory_context,
            runtime_context=runtime_context,
            patch_mode=patch_mode,
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
        context: AgentContext,
        plan: PlanDraft,
        skill_name: str,
        runtime_context: str,
        memory_context: str = "",
        patch_mode: str = "create_new",
        total_llm_calls: int = 0,
        memory_hits: Optional[List[dict]] = None,
    ) -> Tuple[CoderArtifactDraft, str, int]:
        slug = skill_name
        files = [
            f"skills/dynamic/{slug}.py",
            f"tests/generated/test_{slug}.py",
        ]
        
        # 1. First Generation
        coder_messages = build_coder_messages(
            plan_json=plan.model_dump_json(),
            skill_name=skill_name,
            memory_context=memory_context,
            runtime_context=runtime_context,
            patch_mode=patch_mode,
        )
        coder_prompt = f"{coder_messages[0]['content']}\n\n{coder_messages[1]['content']}"
        
        # Global ceiling check
        if total_llm_calls >= 15:
             return CoderArtifactDraft(files=[], rationale="GLOBAL_CEILING_REACHED"), False, total_llm_calls

        code_text = ""
        iteration = 1
        MAX_ITERATIONS = 3
        
        while iteration <= MAX_ITERATIONS:
            try:
                # Use current local LLM generation logic
                raw_response = str(self.llm_client.generate(prompt=coder_prompt)).strip()
                total_llm_calls += 1
                
                # Robust extraction
                code_text = raw_response
                
                # Try to find a JSON block first if it exists
                if "```json" in code_text:
                    json_str = code_text.split("```json")[1].split("```")[0].strip()
                    try:
                        data = json.loads(json_str)
                        for key in ["code", "generated_code", "python_code", "content"]:
                            if isinstance(data, dict) and key in data:
                                code_text = data[key]
                                break
                    except:
                        pass

                # Then handle Markdown fences for Python
                if "```python" in code_text:
                    code_text = code_text.split("```python")[1].split("```")[0].strip()
                elif "```" in code_text:
                    # Only split if it looks like it's wrapping something
                    parts = code_text.split("```")
                    if len(parts) >= 3:
                        code_text = parts[1].strip()
                
                # Final check if the whole thing is JSON braces
                if not code_text.startswith("import") and not code_text.startswith("from") and code_text.strip().startswith("{") and code_text.strip().endswith("}"):
                    try:
                        data = json.loads(code_text)
                        for key in ["code", "generated_code", "python_code", "content"]:
                            if isinstance(data, dict) and key in data:
                                code_text = data[key]
                                break
                    except:
                        pass
                
            except Exception:
                break
                
            # Lớp bảo vệ 1: Static Analysis (ast.parse)
            try:
                tree = ast.parse(code_text)
                # Check for 'run' function
                run_def = None
                for node in ast.walk(tree):
                    if (isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef)) and node.name == "run":
                        run_def = node
                        break
                        
                if not run_def:
                    raise ValueError("MANDATORY 'def run(input_data=None, **kwargs)' function is missing or misnamed.")
                
                if isinstance(run_def, ast.AsyncFunctionDef):
                    raise ValueError("Skill function MUST be synchronous. 'async def' is forbidden.")
                
                # Check for **kwargs
                has_kwargs = any(isinstance(arg, ast.arg) and arg.arg == "kwargs" for arg in run_def.args.args) or run_def.args.kwarg is not None
                if not has_kwargs:
                    raise ValueError("MANDATORY 'run' function must accept '**kwargs' for future-proofing.")
                    
            except (SyntaxError, ValueError) as e:
                coder_prompt += f"\n\n## Syntax or Contract Error (Iteration {iteration})\n{str(e)}\n\nLàm ơn sửa lại code. Phải có hàm 'def run(input_data=None, **kwargs)' đồng bộ (synchronous)."
                iteration += 1
                continue

            # Lớp bảo vệ 2: Code Reviewer Agent
            res_review = self.reviewer.act(
                AgentContext(task_id="review", trace_id=context.trace_id, prompt=skill_name),
                {
                    "plan_json": plan.model_dump_json(),
                    "code_text": code_text,
                    "iteration": iteration
                }
            )
            total_llm_calls += 1
            
            review = res_review.payload.get("verdict", {})
            if review.get("is_approved"):
                break
            
            # Recursive feedback
            coder_prompt += f"\n\n## Feedback từ Reviewer (Vòng {iteration})\n"
            coder_prompt += f"{review.get('review_feedback')}\n"
            iteration += 1

        return CoderArtifactDraft(files=files, rationale=f"Approved on round {iteration}", generated_code=code_text), True, total_llm_calls

    def act(
        self,
        context: AgentContext,
        inputs: Dict[str, object],
    ) -> AgentResult:
        plan_data = inputs.get("plan")
        if not isinstance(plan_data, dict):
            return AgentResult(success=False, reason_code="VALIDATION_FAILED")

        if "task_summary" not in plan_data and "objective" in plan_data:
            objective = str(plan_data.get("objective", "")).strip()
            raw_steps = plan_data.get("steps")
            if isinstance(raw_steps, list):
                steps = [str(item).strip() for item in raw_steps if str(item).strip()]
            else:
                steps = []
            plan_data = {
                "task_summary": objective,
                "confidence": float(plan_data.get("confidence", 0.5)),
                "skills_to_create": [
                    {
                        "skill_name": str(plan_data.get("skill_name", "generated_skill")),
                        "skill_purpose": objective or context.prompt,
                        "coder_notes": "\n".join(steps) if steps else (objective or context.prompt),
                    }
                ],
            }

        plan = PlanDraft(**plan_data)
        memory_context = ""
        if self.rag_service is not None:
            memory_context = self.rag_service.build_context(
                query_text=plan.task_summary,
                top_k=3,
            )

        if self.budget_enforcer is not None:
            user_id = str(context.metadata.get("user_id", "system"))
            org_id = str(context.metadata.get("org_id", "default"))
            plan_text = (
                f"{plan.task_summary} {memory_context}".strip()
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

        runtime_context = inputs.get("runtime_context", "")
        if not runtime_context:
            runtime_context = build_runtime_context(history=inputs.get("history", []))

        total_llm_calls = int(inputs.get("total_llm_calls", 0))

        artifacts, llm_used, total_llm_calls = self.generate_artifacts(
            context=context,
            plan=plan,
            skill_name=str(inputs.get("skill_name", "generated_skill")),
            runtime_context=runtime_context,
            patch_mode=str(inputs.get("patch_mode", "create_new")),
            memory_hits=inputs.get("memory_hits"),
            memory_context=memory_context,
            total_llm_calls=total_llm_calls,
        )

        skill_name = str(inputs.get("skill_name", "generated_skill"))
        rationale, rationale_llm_used = self._build_llm_rationale(
            plan=plan,
            skill_name=skill_name,
            memory_context=memory_context,
            runtime_context=str(runtime_context),
            patch_mode=str(inputs.get("patch_mode", "create_new")),
            fallback=artifacts.rationale,
        )
        artifacts.rationale = rationale
        llm_used = llm_used or rationale_llm_used

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
                    f"objective={plan.task_summary}\n"
                    f"rationale={artifacts.rationale}"
                ),
                metadata={"type": "code", "task_id": context.task_id},
            )
        return AgentResult(
            success=True,
            payload={
                "artifacts": artifacts.model_dump(),
                "total_llm_calls": total_llm_calls,
                "debug": {
                    "llm_used": llm_used,
                    "llm_debug": llm_debug,
                    "memory_context": memory_context,
                },
            },
        )
