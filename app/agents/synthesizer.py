"""Synthesizer agent implementation (v2.0)."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from app.agents.base_agent import AgentContext, AgentResult, BaseAgent
from app.brain.prompt_templates import SYNTHESIZER_SYSTEM_PROMPT, SYNTHESIZER_USER_TEMPLATE

logger = logging.getLogger(__name__)

class SynthesizerAgent(BaseAgent):
    name = "synthesizer"

    def __init__(self, llm_client: Any = None) -> None:
        self.llm_client = llm_client

    async def act(
        self,
        context: AgentContext,
        inputs: Dict[str, Any],
    ) -> AgentResult:
        execution_context_str = inputs.get("execution_context_str", "")
        step_results = inputs.get("step_results", {})
        errors = inputs.get("errors", [])
        
        sys_prompt = SYNTHESIZER_SYSTEM_PROMPT
        user_prompt = SYNTHESIZER_USER_TEMPLATE.format(
            user_request=context.prompt,
            execution_context=execution_context_str,
            step_results=json.dumps(step_results, ensure_ascii=False),
            errors=json.dumps(errors, ensure_ascii=False)
        )
        
        try:
            raw = await self.llm_client.generate_async(sys_prompt + "\n\n" + user_prompt)
            synthesis = json.loads(raw)
            # Ensure unified 'reply' key for frontend UI delivery
            if "reply" not in synthesis:
                synthesis["reply"] = synthesis.get("core_execution_summary", str(synthesis))
                
            return AgentResult(
                success=True, 
                payload={
                    "status": "success",
                    "synthesis_output": synthesis,
                    "next_phase": "delivery"
                }
            )
        except json.JSONDecodeError:
            return AgentResult(
                success=False,
                reason_code="INVALID_JSON",
                payload={"error": "Synthesizer returned invalid JSON."}
            )
        except Exception as exc:
            logger.exception("Synthesizer error")
            return AgentResult(
                success=False, 
                reason_code="SYNTHESIS_ERROR", 
                payload={"error": str(exc)}
            )
