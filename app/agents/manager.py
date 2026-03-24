"""Master Orchestrator / Pipeline Manager (v2.0)."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone as dt_timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.agents.base_agent import AgentContext
from app.agents.context_injector import ContextInjectorAgent
from app.agents.intent_parser import IntentParserAgent
from app.agents.planner import PlannerAgent
from app.agents.skill_router import SkillRouterAgent
from app.agents.coder import CoderAgent
from app.agents.reviewer import ReviewerAgent
from app.agents.skill_runner import SkillRunnerAgent
from app.agents.result_validator import ResultValidatorAgent
from app.agents.synthesizer import SynthesizerAgent
from app.agents.error_handler import ErrorHandlerAgent
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class UnifiedPipelineManager:
    """The explicit 10-Phase State Machine Orchestrator for AIOS."""
    
    def __init__(self, llm_client: Any) -> None:
        self.llm_client = llm_client
        self.settings = get_settings()
        
        # Initialize the 10 nodes
        self.nodes = {
            "context_injector": ContextInjectorAgent(llm_client),
            "intent_parser": IntentParserAgent(llm_client),
            "planner": PlannerAgent(llm_client),
            "skill_router": SkillRouterAgent(llm_client),
            "coder": CoderAgent(llm_client),     # Reviewer is initialized inside Coder for tight loop
            "skill_runner": SkillRunnerAgent(),  # Sandbox integration wrapped here
            "result_validator": ResultValidatorAgent(llm_client),
            "synthesizer": SynthesizerAgent(llm_client),
            "error_handler": ErrorHandlerAgent(llm_client),
            "delivery": None # Terminal state
        }

    async def run_pipeline(
        self,
        task_id: str,
        user_prompt: str,
        history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute the 10-phase pipeline loop until Delivery or ABORT."""
        
        # State Machine memory
        pipeline_state = {
            "task_id": task_id,
            "original_prompt": user_prompt,
            "history": history or [],
            "current_phase": "context_injector",
            "execution_context": {},
            "intent_output": {},
            "plan_output": {},
            "router_output": {},
            "skill_outputs": {},
            "validation_results": {},
            "synthesis_output": {},
            "errors": [],
            "debug_trace": []
        }
        
        max_hops = 25
        hop_count = 0
        
        while pipeline_state["current_phase"] != "delivery" and hop_count < max_hops:
            hop_count += 1
            current_phase = pipeline_state["current_phase"]
            
            logger.info(f"Pipeline [Hop {hop_count}]: Executing >> {current_phase.upper()}")
            pipeline_state["debug_trace"].append(f"ENTER: {current_phase}")
            
            node = self.nodes.get(current_phase)
            if not node:
                raise ValueError(f"Unknown phase requested: {current_phase}")
                
            try:
                # Dispatch based on phase
                if current_phase == "context_injector":
                    res = await node.act(AgentContext(task_id, f"ctx-{task_id}", user_prompt), {"history": pipeline_state["history"]})
                    if res.success:
                        pipeline_state["execution_context"] = res.payload
                        pipeline_state["current_phase"] = "intent_parser"
                    else:
                        raise Exception(res.payload.get("error"))
                        
                elif current_phase == "intent_parser":
                    res = await node.act(
                        AgentContext(task_id, f"intent-{task_id}", user_prompt), 
                        {"message": user_prompt, "runtime_context_str": pipeline_state["execution_context"].get("runtime_context_str")}
                    )
                    if res.success:
                        pipeline_state["intent_output"] = res.payload.get("intent_output", {})
                        pipeline_state["current_phase"] = res.payload.get("next_phase", "error_handler")
                        if not res.payload.get("proceed_to_phase3"):
                            pipeline_state["synthesis_output"] = {"reply": res.payload.get("clarification")}
                            pipeline_state["current_phase"] = "delivery"
                    else:
                        raise Exception(res.payload.get("error"))
                        
                elif current_phase == "planner":
                    res = await node.act(
                        AgentContext(task_id, f"plan-{task_id}", user_prompt),
                        {"intent_output": pipeline_state["intent_output"], "runtime_context_str": pipeline_state["execution_context"].get("runtime_context_str")}
                    )
                    if res.success:
                        pipeline_state["plan_output"] = res.payload.get("execution_plan", {})
                        print(f"\n[DEBUG] PLANNER OUTPUT KEYS: {list(pipeline_state['plan_output'].keys())}")
                        pipeline_state["current_phase"] = res.payload.get("next_phase", "skill_router")
                    else:
                        raise Exception(res.payload.get("error"))
                        
                elif current_phase == "skill_router":
                    tools_status = self._get_tools_status()
                    res = await node.act(
                        AgentContext(task_id, f"router-{task_id}", user_prompt),
                        {
                            "execution_plan": pipeline_state["plan_output"], 
                            "runtime_context_str": pipeline_state["execution_context"].get("runtime_context_str"),
                            "tools_status": tools_status
                        }
                    )
                    if res.success:
                        pipeline_state["router_output"] = res.payload
                        if res.payload.get("skills_to_build"):
                            pipeline_state["current_phase"] = "coder"
                        else:
                            pipeline_state["current_phase"] = "skill_runner"
                    else:
                        raise Exception(res.payload.get("error"))
                        
                elif current_phase == "coder":
                    skills_to_build = pipeline_state["router_output"].get("skills_to_build", [])
                    if not skills_to_build:
                        pipeline_state["current_phase"] = "skill_runner"
                        continue
                        
                    res = await node.act(
                        AgentContext(task_id, f"code-{task_id}", user_prompt),
                        {
                            "step_id": skills_to_build[0], 
                            "requirement": f"Create skill: {skills_to_build[0]} according to planner.", 
                            "mode": "create",
                            "plan_output": pipeline_state["plan_output"],
                            "execution_context": pipeline_state["execution_context"]
                        }
                    )
                    if res.success:
                        # Register dynamically created tool
                        pipeline_state["current_phase"] = res.payload.get("next_phase", "error_handler")
                    else:
                        raise Exception(res.payload.get("error"))
                        
                elif current_phase == "skill_runner":
                    res = await node.act(
                        AgentContext(task_id, f"run-{task_id}", user_prompt),
                        {"steps_to_execute": pipeline_state["plan_output"].get("steps", []), "parallelizable_groups": pipeline_state["plan_output"].get("parallelizable_groups", [])}
                    )
                    if res.success:
                        pipeline_state["skill_outputs"] = res.payload.get("step_results", {})
                        pipeline_state["current_phase"] = res.payload.get("next_phase", "result_validator")
                    else:
                        raise Exception(res.payload.get("error"))
                        
                elif current_phase == "result_validator":
                    attempt = pipeline_state.get("validation_attempts", 0) + 1
                    pipeline_state["validation_attempts"] = attempt
                    res = await node.act(
                        AgentContext(task_id, f"validate-{task_id}", user_prompt),
                        {"skill_runner_output": pipeline_state["skill_outputs"], "attempt": attempt}
                    )
                    if res.success:
                        pipeline_state["validation_results"] = res.payload
                        pipeline_state["current_phase"] = res.payload.get("next_phase", "synthesizer")
                    else:
                        raise Exception(res.payload.get("error"))
                        
                elif current_phase == "synthesizer":
                    res = await node.act(
                        AgentContext(task_id, f"synth-{task_id}", user_prompt),
                        {
                            "execution_context_str": pipeline_state["execution_context"].get("runtime_context_str", ""),
                            "step_results": pipeline_state["skill_outputs"],
                            "errors": pipeline_state["errors"]
                        }
                    )
                    if res.success:
                        pipeline_state["synthesis_output"] = res.payload.get("synthesis_output", {})
                        pipeline_state["current_phase"] = "delivery"
                    else:
                        raise Exception(res.payload.get("error"))
                        
                elif current_phase == "error_handler":
                    last_error = pipeline_state["errors"][-1] if pipeline_state["errors"] else {"tier": 3, "message": "Unknown error routed to handler."}
                    res = await node.act(
                        AgentContext(task_id, f"error-{task_id}", user_prompt),
                        {"error_info": last_error}
                    )
                    if res.success:
                        pipeline_state["synthesis_output"] = {"reply": res.payload.get("error_response", {}).get("explanation", "Lỗi rùi.")}
                        pipeline_state["current_phase"] = res.payload.get("next_phase", "delivery")
                    else:
                        pipeline_state["current_phase"] = "delivery"

            except Exception as loop_err:
                import traceback
                traceback.print_exc()
                pipeline_state["errors"].append({
                    "phase": current_phase,
                    "message": str(loop_err),
                    "tier": 1 if "timeout" in str(loop_err).lower() else 3,
                    "context": {"attempt": 1}
                })
                pipeline_state["current_phase"] = "error_handler"

        if hop_count >= max_hops:
            logger.error("Pipeline reached maximum hop count (infinite loop aborted).")
            pipeline_state["synthesis_output"] = {"reply": "Hệ thống bị treo do lặp quá nhiều lần. Đã hủy bỏ tác vụ."}
            
        return pipeline_state

    def _get_tools_status(self) -> Dict[str, str]:
        """Scan static and dynamic skills to see what's available."""
        tools = {}
        paths = [
            Path("app/skills/static"),
            Path("app/skills/dynamic")
        ]
        for p in paths:
            if p.exists():
                for f in p.glob("*.py"):
                    if f.name != "__init__.py":
                        name = f.stem.replace("_", "-")
                        tools[name] = "healthy"
        return tools

# =========================================================================================
# Legacy Interface compatibility export (for existing CLIs or runners missing _run_cli_style_chat_pipeline)
# =========================================================================================

async def _run_cli_style_chat_pipeline(manager, task_id: str, prompt: str, history=None) -> tuple:
    """Compatibility shim returning (plan_data, execution_outputs, exec_summary, pipeline_debug)."""
    if isinstance(manager, UnifiedPipelineManager):
        result = await manager.run_pipeline(task_id, prompt, history)
        
        # Unpack to match legacy tuple
        plan_data = result.get("plan_output", {})
        execution_outputs = list(result.get("skill_outputs", {}).values())
        exec_summary = result.get("synthesis_output", {}).get("reply", "Task Completed.")
        pipeline_debug = result.get("debug_trace", [])
        return plan_data, execution_outputs, exec_summary, pipeline_debug
        
    # If legacy manager exists
    res = await manager.run(task_id, prompt, history)
    artifacts = res.artifacts if hasattr(res, "artifacts") else {}
    return {}, res.execution_results, res.reply, artifacts
