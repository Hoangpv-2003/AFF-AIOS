"""Error Handler agent implementation (v2.0)."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from app.agents.base_agent import AgentContext, AgentResult, BaseAgent
from app.brain.prompt_templates import ERROR_HANDLER_SYSTEM_PROMPT, ERROR_HANDLER_USER_TEMPLATE

logger = logging.getLogger(__name__)

class ErrorHandlerAgent(BaseAgent):
    name = "error_handler"

    def __init__(self, llm_client: Any = None) -> None:
        self.llm_client = llm_client

    def _determine_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff + jitter."""
        import random
        base = min(0.5 * (2 ** attempt), 30.0)
        return base + (base * random.uniform(0, 0.1))

    async def act(
        self,
        context: AgentContext,
        inputs: Dict[str, Any],
    ) -> AgentResult:
        error_info = inputs.get("error_info", {})
        
        # If it's a programmatic direct call rather than LLM reasoning
        if hasattr(self, "llm_client") and self.llm_client:
            sys_prompt = ERROR_HANDLER_SYSTEM_PROMPT
            user_prompt = ERROR_HANDLER_USER_TEMPLATE.format(
                error_info=json.dumps(error_info, ensure_ascii=False)
            )
            
            try:
                raw = await self.llm_client.generate_async(sys_prompt + "\n\n" + user_prompt)
                handling = json.loads(raw)
            except Exception as e:
                logger.error(f"Error LLM crashed: {e}")
                handling = {}
        else:
            handling = {}
            
        tier = error_info.get("tier", 3)
        attempt = error_info.get("context", {}).get("attempt", 1)
        
        if not handling:
            # Fallback logic if LLM fails
            handling = {
                "status": "escalated" if tier == 3 else "handled",
                "recovery_strategy": "AUTO" if tier == 1 else "USER_INPUT" if tier == 2 else "ABORT",
                "error_response": {
                    "error_id": error_info.get("error_id", "ERR_UKN"),
                    "problem": error_info.get("message", "Unknown error"),
                    "root_cause": "Failed to parse error fully.",
                    "explanation": error_info.get("message", ""),
                    "user_options": [],
                    "can_retry": tier == 1
                }
            }

        if handling.get("recovery_strategy") == "AUTO" and tier == 1:
            delay = self._determine_backoff(attempt)
            handling["recovery_action"] = f"Retry after {delay:.2f}s"
            # In orchestration this would call asyncio.sleep(delay)
            
        handling["next_phase"] = error_info.get("phase", "delivery") if handling.get("recovery_strategy") == "AUTO" else "delivery"
            
        return AgentResult(
            success=True,
            payload=handling
        )
