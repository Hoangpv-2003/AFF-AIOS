"""Result Validator agent implementation (v2.0)."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from app.agents.base_agent import AgentContext, AgentResult, BaseAgent
from app.brain.prompt_templates import VALIDATOR_SYSTEM_PROMPT, VALIDATOR_USER_TEMPLATE
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class ResultValidatorAgent(BaseAgent):
    name = "result_validator"

    def __init__(self, llm_client: Any = None) -> None:
        self.llm_client = llm_client
        self.settings = get_settings()

    async def act(
        self,
        context: AgentContext,
        inputs: Dict[str, Any],
    ) -> AgentResult:
        skill_runner_output = inputs.get("skill_runner_output", {})
        attempt = inputs.get("attempt", 1)
        
        sys_prompt = VALIDATOR_SYSTEM_PROMPT
        user_prompt = VALIDATOR_USER_TEMPLATE.format(
            skill_outputs=json.dumps(skill_runner_output, ensure_ascii=False),
            attempt=attempt
        )
        
        try:
            raw = await self.llm_client.generate_async(prompt=sys_prompt + "\n\n" + user_prompt)
            validation_decision = json.loads(raw)
            
            # Enforce max attempts explicitly if LLM hallucinated
            status_val = validation_decision.get("status", "pass")
            if status_val == "fail_retry" and attempt >= self.settings.MAX_VALIDATOR_RETRIES:
                logger.warning(f"Validator retry exhausted ({attempt}/{self.settings.MAX_VALIDATOR_RETRIES}). Aborting.")
                validation_decision["status"] = "fail_abort"
                status_val = "fail_abort"
                
            status_map = {
                "pass": "synthesizer",
                "fail_retry": "planner",
                "fail_abort": "error_handler"
            }
            
            validation_decision["next_phase"] = status_map.get(status_val, "error_handler")
            
            return AgentResult(success=True, payload=validation_decision)
            
        except json.JSONDecodeError:
            return AgentResult(
                success=False,
                reason_code="INVALID_JSON",
                payload={"error": "Result Validator did not return valid JSON."}
            )
        except Exception as exc:
            logger.exception("Validator error")
            return AgentResult(
                success=False, 
                reason_code="VALIDATION_ERROR", 
                payload={"error": str(exc)}
            )
