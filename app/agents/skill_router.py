"""Skill Router agent implementation."""

from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from app.agents.base_agent import AgentContext, AgentResult, BaseAgent
from app.brain.prompt_templates import build_skill_router_messages, build_runtime_context

class SkillRouterAgent(BaseAgent):
    name = "skill_router"

    def __init__(self, llm_client: Any = None) -> None:
        self.llm_client = llm_client

    def act(
        self,
        context: AgentContext,
        inputs: Dict[str, Any],
    ) -> AgentResult:
        plan_json = inputs.get("plan_json", "")
        data_sources = inputs.get("data_sources", "")
        available_skills = inputs.get("available_skills", "")
        runtime_context = inputs.get("runtime_context", "")
        if not runtime_context:
            runtime_context = build_runtime_context(history=inputs.get("history", []))

        messages = build_skill_router_messages(plan_json, available_skills, runtime_context, data_sources)
        full_prompt = f"{messages[0]['content']}\n\n{messages[1]['content']}"

        try:
            raw = self.llm_client.generate(prompt=full_prompt, response_format="json")
            data = json.loads(raw)
            # Normalize labels (Option B)
            if data.get("route") == "create_new": data["route"] = "CREATE"
            if data.get("route") == "patch": data["route"] = "MODIFY"
            
            return AgentResult(success=True, payload=data)
        except Exception as exc:
            return AgentResult(
                success=False, 
                reason_code="PARSING_ERROR", 
                payload={"error": str(exc)}
            )
