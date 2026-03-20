"""Intent Parser agent implementation."""

from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from app.agents.base_agent import AgentContext, AgentResult, BaseAgent
from app.brain.prompt_templates import build_intent_parser_messages, build_runtime_context

class IntentParserAgent(BaseAgent):
    name = "intent_parser"

    def __init__(self, llm_client: Any = None) -> None:
        self.llm_client = llm_client

    def act(
        self,
        context: AgentContext,
        inputs: Dict[str, Any],
    ) -> AgentResult:
        user_message = inputs.get("message", context.prompt)
        runtime_context = inputs.get("runtime_context", "")
        memory_context = inputs.get("memory_context", "")
        if not runtime_context:
            runtime_context = build_runtime_context(history=inputs.get("history", []))

        messages = build_intent_parser_messages(user_message, runtime_context, memory_context)
        # Join messages for non-chat LLM client if needed, 
        # but here we assume the client handles system/user separation if possible.
        # For simplicity with current _generate_text_strict pattern:
        full_prompt = f"{messages[0]['content']}\n\n{messages[1]['content']}"

        try:
            # Assuming llm_client.generate exists as per agents.py pattern
            raw = self.llm_client.generate(prompt=full_prompt, response_format="json")
            intent = json.loads(raw)
            
            # Ensure defaults
            intent.setdefault("confidence", 1.0)
            intent.setdefault("ambiguous", False)
            intent.setdefault("clarification_needed", False)
            
            return AgentResult(success=True, payload=intent)
        except Exception as exc:
            return AgentResult(
                success=False, 
                reason_code="PARSING_ERROR", 
                payload={"error": str(exc)}
            )
