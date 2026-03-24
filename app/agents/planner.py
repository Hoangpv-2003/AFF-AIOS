"""Planner agent implementation (v2.0) with DAG Cycle Detection."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Set

from app.agents.base_agent import AgentContext, AgentResult, BaseAgent
from app.brain.prompt_templates import PLANNER_SYSTEM_PROMPT, PLANNER_USER_TEMPLATE

logger = logging.getLogger(__name__)

class PlannerAgent(BaseAgent):
    name = "planner"

    def __init__(self, llm_client: Any = None) -> None:
        self.llm_client = llm_client

    def _detect_cycles(self, steps: List[Dict[str, Any]]) -> List[List[str]]:
        """DFS-based cycle detection algorithm."""
        graph: Dict[str, List[str]] = {s["step_id"]: s.get("depends_on", []) for s in steps}
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        cycles: List[List[str]] = []
        path: List[str] = []

        def dfs(node: str):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Cycle detected
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:].copy() + [neighbor])
            
            rec_stack.remove(node)
            path.pop()

        for node in graph:
            if node not in visited:
                dfs(node)
                
        return cycles

    async def act(
        self,
        context: AgentContext,
        inputs: Dict[str, Any],
    ) -> AgentResult:
        intent_json = inputs.get("intent_output", {})
        runtime_context_str = inputs.get("runtime_context_str", "")
        execution_context = inputs.get("execution_context", {})

        user_prompt = PLANNER_USER_TEMPLATE.format(
            runtime_context=runtime_context_str,
            memory_context="[]",
            validator_feedback="[]",
            intent_json=json.dumps(intent_json, ensure_ascii=False),
            planning_mode="standard"
        )
        full_prompt = f"{PLANNER_SYSTEM_PROMPT}\n\n{user_prompt}"

        try:
            raw = await self.llm_client.generate_async(prompt=full_prompt)
            plan = json.loads(raw)
            
            # DFS Cycle Detection
            steps = plan.get("steps", [])
            cycles = self._detect_cycles(steps)
            
            if cycles:
                logger.warning(f"Circular dependency detected by Planner Node: {cycles}")
                return AgentResult(
                    success=False, # We use success=False internally to indicate an error state in the agent graph, but map it to "error" status
                    payload={
                        "status": "error",
                        "circular_dependency": {
                            "detected": True,
                            "cycles": cycles,
                            "explanation": f"Detected circular dependency in steps: {cycles}",
                            "user_action_needed": "Please clarify step dependencies."
                        },
                        "next_phase": "error_handler"
                    }
                )
                
            return AgentResult(
                success=True,
                payload={
                    "status": "success",
                    "execution_plan": plan,
                    "next_phase": "skill_router"
                }
            )
            
        except json.JSONDecodeError:
            return AgentResult(
                success=False,
                reason_code="INVALID_JSON",
                payload={"status": "error", "error": "LLM did not return valid JSON plan."}
            )
        except Exception as exc:
            logger.exception("Planner error")
            return AgentResult(
                success=False, 
                reason_code="PLANNING_ERROR", 
                payload={"status": "error", "error": str(exc)}
            )
