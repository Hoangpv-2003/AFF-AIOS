"""Error Handler agent implementation."""

from __future__ import annotations
import json
from typing import Any, Dict, Optional
from app.agents.base_agent import AgentContext, AgentResult, BaseAgent
from app.brain.prompt_templates import build_error_handler_messages

class ErrorHandlerAgent(BaseAgent):
    name = "error_handler"

    def __init__(self, llm_client: Any = None) -> None:
        self.llm_client = llm_client

    def act(
        self,
        context: AgentContext,
        inputs: Dict[str, Any],
    ) -> AgentResult:
        failure_stage = inputs.get("failure_stage", "Unknown")
        technical_error = inputs.get("technical_error", "No details")

        messages = build_error_handler_messages(failure_stage, technical_error)
        full_prompt = f"{messages[0]['content']}\n\n{messages[1]['content']}"

        try:
            raw = self.llm_client.generate(prompt=full_prompt, response_format="json")
            data = json.loads(raw)
            return AgentResult(success=True, payload=data)
        except Exception as exc:
            return AgentResult(
                success=False, 
                reason_code="PARSING_ERROR", 
                payload={"error": str(exc), "user_message": "Tôi gặp sự cố kỹ thuật. Vui lòng thử lại sau."}
            )
