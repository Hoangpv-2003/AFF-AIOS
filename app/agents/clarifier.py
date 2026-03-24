"""Clarifier agent implementation."""

from __future__ import annotations
import json
from typing import Any, Dict, Optional
from app.agents.base_agent import AgentContext, AgentResult, BaseAgent
from app.brain.prompt_templates import build_clarifier_messages

class ClarifierAgent(BaseAgent):
    name = "clarifier"

    def __init__(self, llm_client: Any = None) -> None:
        self.llm_client = llm_client

    async def act(
        self,
        context: AgentContext,
        inputs: Dict[str, Any],
    ) -> AgentResult:
        user_message = inputs.get("message", context.prompt)
        hint = inputs.get("hint", "")

        messages = build_clarifier_messages(user_message, hint)
        full_prompt = f"{messages[0]['content']}\n\n{messages[1]['content']}"

        try:
            raw = await self.llm_client.generate_async(prompt=full_prompt)
            data = json.loads(raw)
            return AgentResult(success=True, payload=data)
        except Exception as exc:
            return AgentResult(
                success=False, 
                reason_code="PARSING_ERROR", 
                payload={"error": str(exc)}
            )
