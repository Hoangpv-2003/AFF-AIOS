"""Coder agent implementation (v2.0)."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from app.agents.base_agent import AgentContext, AgentResult, BaseAgent
from app.agents.reviewer import ReviewerAgent
from app.brain.prompt_templates import CODER_SYSTEM_PROMPT, CODER_USER_TEMPLATE
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class CoderAgent(BaseAgent):
    name = "coder"

    def __init__(
        self,
        llm_client: Any = None,
        reviewer: ReviewerAgent | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.reviewer = reviewer or ReviewerAgent(llm_client=llm_client)
        self.settings = get_settings()

    def _extract_code(self, raw: str) -> str:
        # 1. Try to parse as JSON structure
        try:
            clean_raw = raw
            if "```json" in clean_raw:
                clean_raw = clean_raw.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_raw and raw.startswith("{"):
                clean_raw = clean_raw.split("```")[1].strip()
                
            parsed = json.loads(clean_raw)
            if "logic" in parsed:
                return str(parsed["logic"])
        except Exception:
            pass
            
        # 2. Fallback to raw string extraction
        if "```python" in raw:
            return raw.split("```python")[1].split("```")[0].strip()
        if "```" in raw:
            parts = raw.split("```")
            return parts[1].strip() if len(parts) >= 3 else raw.strip()
        return raw.strip()

    async def act(
        self,
        context: AgentContext,
        inputs: Dict[str, Any],
    ) -> AgentResult:
        step_id = inputs.get("step_id", "unknown")
        requirement = inputs.get("requirement", "")
        mode = inputs.get("mode", "create")
        plan_json = inputs.get("plan_output", {})
        execution_context = inputs.get("execution_context", {})
        runtime_context_str = execution_context.get("runtime_context_str", "")
        
        max_rounds = self.settings.MAX_CODE_REVIEW_ROUNDS if mode == "create" else 2
        
        sys_prompt = CODER_SYSTEM_PROMPT.replace("{current_datetime}", "UTC").replace("{timezone}", "UTC").replace("{locale}", "en-US")
        base_user_prompt = CODER_USER_TEMPLATE.format(
            runtime_context=runtime_context_str,
            plan_json=json.dumps(plan_json, ensure_ascii=False),
            coder_brief=requirement,
            memory_context="",
            skill_contract_json="{}",
            skill_name=step_id,
            patch_mode=mode
        )
        
        current_code = ""
        reviews = []
        final_approval = False
        iteration = 1
        
        while iteration <= max_rounds:
            # 1. Generate code
            user_prompt = base_user_prompt
            if reviews:
                user_prompt += f"\n\n## Feedback from Previous Round (Round {iteration-1})\n{json.dumps(reviews[-1], indent=2)}\n\nPlease apply fixes and return the full updated code block."
            
            try:
                raw_code_resp = await self.llm_client.generate_async(prompt=sys_prompt + "\n\n" + user_prompt)
                current_code = self._extract_code(raw_code_resp)
            except Exception as e:
                logger.error(f"Coder LLM error: {e}")
                break
                
            # 2. Review code
            review_res = await self.reviewer.act(
                context, 
                {"code_text": current_code, "iteration": iteration, "plan_output": plan_json}
            )
            
            if not review_res.success:
                break
                
            review_data = review_res.payload
            reviews.append(review_data)
            
            if review_data.get("action") == "APPROVED" or review_data.get("is_approved") is True:
                final_approval = True
                break
                
            iteration += 1

        assessment = "PRODUCTION" if final_approval else "REJECTED"
        
        file_path = None
        if current_code:  # Save ALWAYS for debugging why it's failing
            import os
            clean_name = str(step_id).replace(" ", "_").replace("-", "_").lower()
            
            if final_approval:
                file_path = f"app/skills/dynamic/{clean_name}.py"
                os.makedirs("app/skills/dynamic", exist_ok=True)
            else:
                file_path = f"app/skills/dynamic/rejected_{clean_name}.py"
                os.makedirs("app/skills/dynamic", exist_ok=True)
                
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(current_code)
            logger.info(f"Successfully generated and saved new dynamic skill: {file_path}")
            
        return AgentResult(
            success=True,
            payload={
                "status": "success" if final_approval else "error",
                "code": current_code,
                "language": "python",
                "reviews": reviews,
                "final_approval": final_approval,
                "quality_assessment": assessment,
                "artifact_path": file_path,
                "tokens_used": 0,
                "completion_time_ms": 0,
                "next_phase": "skill_runner" if final_approval else "error_handler"
            }
        )
