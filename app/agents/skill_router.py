"""Skill Router agent implementation (v2.0)."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from app.agents.base_agent import AgentContext, AgentResult, BaseAgent
from app.brain.prompt_templates import SKILL_ROUTER_SYSTEM_PROMPT, SKILL_ROUTER_USER_TEMPLATE

logger = logging.getLogger(__name__)

class SkillRouterAgent(BaseAgent):
    name = "skill_router"

    def __init__(self, llm_client: Any = None) -> None:
        self.llm_client = llm_client

    async def act(
        self,
        context: AgentContext,
        inputs: Dict[str, Any],
    ) -> AgentResult:
        plan_json = inputs.get("execution_plan", {})
        tools_status = inputs.get("tools_status", {})
        runtime_context_str = inputs.get("runtime_context_str", "")

        full_prompt = f"{SKILL_ROUTER_SYSTEM_PROMPT}\n\n{SKILL_ROUTER_USER_TEMPLATE.format(runtime_context=runtime_context_str, plan_json=json.dumps(plan_json, ensure_ascii=False), available_skills=json.dumps(tools_status, ensure_ascii=False))}"

        try:
            raw = await self.llm_client.generate_async(prompt=full_prompt)
            router_decision = json.loads(raw)
            
            # `router_decision` should match `SkillRouterResponse` structure
            router_decision["status"] = "success"
            router_decision["next_phase"] = "realtime_fetcher" if router_decision.get("realtime_queries") else "coder" if router_decision.get("skills_to_build") else "skill_runner"
            
            return AgentResult(
                success=True,
                payload=router_decision
            )
        except json.JSONDecodeError:
            return AgentResult(
                success=False,
                reason_code="INVALID_JSON",
                payload={"error": "Skill Router did not return valid JSON."}
            )
        except Exception as exc:
            logger.exception("Skill Router error")
            return AgentResult(
                success=False, 
                reason_code="ROUTING_ERROR", 
                payload={"error": str(exc)}
            )
