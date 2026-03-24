"""Context Injector agent for environment and history injection (v2.0)."""

from __future__ import annotations

import datetime
from typing import Any, Dict

from app.agents.base_agent import AgentContext, AgentResult, BaseAgent
from app.brain.prompt_templates import CONTEXT_INJECTOR_TEMPLATE


class ContextInjectorAgent(BaseAgent):
    name = "context_injector"

    def __init__(self, llm_client: Any | None = None) -> None:
        self.llm_client = llm_client

    async def act(
        self,
        context: AgentContext,
        inputs: Dict[str, Any],
    ) -> AgentResult:
        try:
            history = inputs.get("history", [])
            timezone_val = inputs.get("timezone", "UTC")
            locale_val = inputs.get("locale", "en-US")
            
            # Format the runtime context variables
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            runtime_context = CONTEXT_INJECTOR_TEMPLATE.format(
                current_datetime=now_utc.isoformat(),
                current_date_human=now_utc.strftime("%A, %d %B %Y"),
                timezone=timezone_val,
                locale=locale_val,
                conversation_turn=len(history) + 1,
                prior_intent_chain="[]"
            )
            
            # Return payload strictly structured for v2_types.ExecutionContext
            payload = {
                "datetime": {
                    "utc_timestamp": now_utc.isoformat(),
                    "server_timezone": "UTC",
                    "user_timezone": timezone_val,
                    "user_locale": locale_val,
                },
                "history": {
                    "total_turns": len(history),
                    "last_n_turns": history[-10:] if history else [],
                    "conversation_id": context.task_id,
                },
                "tools_status": {
                    "rag_memory_search": "Search local database for project code, docs, and architecture memory. Args: query (str)",
                    "web_search": "Fetch live internet data. Args: query (str)",
                    "python_sandbox": "Execute a dynamic python script to fetch APIs or perform math. Args: code (str)",
                    "cli_agent": "Run local bash/powershell commands safely. Args: command (str)"
                },
                "runtime_context_str": runtime_context
            }
            
            return AgentResult(
                success=True,
                payload=payload,
            )
        except Exception as e:
            return AgentResult(
                success=False,
                reason_code="CONTEXT_INJECTION_FAILED",
                payload={"error": str(e)},
            )
