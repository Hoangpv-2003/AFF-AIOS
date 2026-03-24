"""Intent Parser agent implementation (v2.0)."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from app.agents.base_agent import AgentContext, AgentResult, BaseAgent
from app.brain.prompt_templates import INTENT_PARSER_SYSTEM_PROMPT, INTENT_PARSER_USER_TEMPLATE
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class IntentParserAgent(BaseAgent):
    name = "intent_parser"

    def __init__(self, llm_client: Any = None) -> None:
        self.llm_client = llm_client
        self.settings = get_settings()

    async def act(
        self,
        context: AgentContext,
        inputs: Dict[str, Any],
    ) -> AgentResult:
        user_message = inputs.get("message", context.prompt)
        runtime_context_str = inputs.get("runtime_context_str", "")
        history_context = inputs.get("history", [])

        sys_prompt = INTENT_PARSER_SYSTEM_PROMPT
        
        user_prompt = INTENT_PARSER_USER_TEMPLATE.format(
            runtime_context=runtime_context_str,
            memory_context=json.dumps(history_context, ensure_ascii=False),
            user_message=user_message
        )
        
        full_prompt = f"{sys_prompt}\n\n{user_prompt}"

        try:
            raw = await self.llm_client.generate_async(prompt=full_prompt)
            intent = json.loads(raw)
            
            # Add status mapping
            if intent.get("clarifications_needed", False) or intent.get("confidence", 1.0) < self.settings.CONFIDENCE_INTENT:
                status = "clarification_needed"
            else:
                status = "success"
                
            return AgentResult(
                success=True,
                payload={
                    "status": status,
                    "intent_output": intent if status == "success" else None,
                    "clarification": intent.get("clarification") if status == "clarification_needed" else None,
                    "next_phase": "planner" if status == "success" else "intent_parser",
                    "proceed_to_phase3": status == "success",
                    "raw_output": intent
                }
            )
        except json.JSONDecodeError:
            logger.error(f"Intent Parser returned invalid JSON: {raw}")
            return AgentResult(
                success=False,
                reason_code="INVALID_JSON",
                payload={"error": "LLM did not return valid JSON.", "raw": raw}
            )
        except Exception as exc:
            logger.exception("Intent Parser error")
            return AgentResult(
                success=False, 
                reason_code="PARSING_ERROR", 
                payload={"error": str(exc)}
            )
