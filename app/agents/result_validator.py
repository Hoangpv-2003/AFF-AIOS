"""Result Validator agent implementation."""

from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from app.agents.base_agent import AgentContext, AgentResult, BaseAgent
from app.brain.prompt_templates import build_result_validator_messages, build_runtime_context

class ResultValidatorAgent(BaseAgent):
    name = "result_validator"

    def __init__(self, llm_client: Any = None) -> None:
        self.llm_client = llm_client

    def act(
        self,
        context: AgentContext,
        inputs: Dict[str, Any],
    ) -> AgentResult:
        original_request = inputs.get("original_request", context.prompt)
        skill_output = inputs.get("skill_output", "{}")
        expected_goal = inputs.get("expected_goal", "")
        runtime_context = inputs.get("runtime_context", "")
        if not runtime_context:
            runtime_context = build_runtime_context(history=inputs.get("history", []))

        messages = build_result_validator_messages(
            original_request, 
            skill_output, 
            expected_goal, 
            runtime_context
        )
        full_prompt = f"{messages[0]['content']}\n\n{messages[1]['content']}"

        try:
            raw = self.llm_client.generate(prompt=full_prompt, response_format="json")
            data = json.loads(raw)
            return AgentResult(success=True, payload=data)
        except Exception as exc:
            return AgentResult(
                success=False, 
                reason_code="PARSING_ERROR", 
                payload={"error": str(exc)}
            )
