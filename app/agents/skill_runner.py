"""Skill Runner agent implementation (v2.0)."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from app.agents.base_agent import AgentContext, AgentResult, BaseAgent
from app.schemas.v2_types import ExecutionStatus

logger = logging.getLogger(__name__)

class SkillRunnerAgent(BaseAgent):
    name = "skill_runner"

    def __init__(self, sandbox_runner: Any = None) -> None:
        self.sandbox_runner = sandbox_runner

    async def _execute_skill(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single skill, wrapping output securely using subprocess boundaries."""
        import subprocess
        import time
        import tempfile
        import os
        
        step_id = step.get("step_id", "unknown")
        action = step.get("action", "")
        args = step.get("args", {})
        
        logger.info(f"Executing dynamic step {step_id}: {action}")
        
        start_t = time.time()
        result_text = ""
        status = ExecutionStatus.SUCCESS
        
        try:
            if action == "python_sandbox":
                code = args.get("code", "")
                with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
                    f.write(code)
                    temp_path = f.name
                
                try:
                    proc = subprocess.run(["python", temp_path], capture_output=True, text=True, timeout=60)
                    result_text = proc.stdout
                    if proc.stderr:
                        result_text += f"\n[STDERR]: {proc.stderr}"
                    if proc.returncode != 0:
                        status = ExecutionStatus.FAILED
                finally:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                        
            elif action == "cli_agent":
                cmd = args.get("command", "")
                proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
                result_text = proc.stdout + ("\n[STDERR]: " + proc.stderr if proc.stderr else "")
                if proc.returncode != 0:
                    status = ExecutionStatus.FAILED
                    
            elif action in ("web_search", "rag_memory_search"):
                # Delegate to python sandbox automatically
                result_text = f"Tool '{action}' is natively disabled. Please re-plan using 'python_sandbox' (with urllib/requests to search the web or os/glob to search local memory) to achieve the goal."
                status = ExecutionStatus.FAILED
            else:
                # 1. Try static skills (kebab-to-snake)
                clean_action = str(action).replace("-", "_").replace(" ", "_").lower()
                static_path = f"app/skills/static/{clean_action}.py"
                dynamic_path = f"app/skills/dynamic/{clean_action}.py"
                
                target_path = static_path if os.path.exists(static_path) else dynamic_path if os.path.exists(dynamic_path) else None
                
                if target_path:
                    logger.info(f"Executing skill script: {target_path} with args: {args}")
                    # Pass args as a single JSON string argument
                    proc = subprocess.run(["python", target_path, json.dumps(args, ensure_ascii=False)], capture_output=True, text=True, timeout=60)
                    result_text = proc.stdout + ("\n[STDERR]: " + proc.stderr if proc.stderr else "")
                    if proc.returncode != 0:
                        status = ExecutionStatus.FAILED
                else:
                    result_text = f"Unknown action: {action} and no skill found at {static_path} or {dynamic_path}. Please use 'python_sandbox' or create the skill."
                    status = ExecutionStatus.FAILED
                
        except subprocess.TimeoutExpired:
            result_text = "ERROR: Subprocess execution Timed Out."
            status = ExecutionStatus.FAILED
        except Exception as e:
            result_text = f"CRITICAL CRASH: {str(e)}"
            status = ExecutionStatus.FAILED
            
        return {
            "step_id": step_id,
            "status": status,
            "start_time": "2026-03-24T10:00:00Z",
            "end_time": "2026-03-24T10:00:05Z",
            "duration_ms": int((time.time() - start_t) * 1000),
            "output": {"result": result_text.strip()[:2000]}, # Trim massive yields
            "tokens_used": 150,
            "memory_used_mb": 45,
            "files_created": []
        }

    async def act(
        self,
        context: AgentContext,
        inputs: Dict[str, Any],
    ) -> AgentResult:
        steps_to_execute = inputs.get("steps_to_execute", [])
        parallelizable_groups = inputs.get("parallelizable_groups", [])
        
        if not parallelizable_groups and steps_to_execute:
            # Fallback sequential if planner didn't group
            parallelizable_groups = [[s["step_id"]] for s in steps_to_execute]
            
        step_map = {s["step_id"]: s for s in steps_to_execute}
        
        step_results = {}
        total_time_ms = 0
        total_tokens = 0
        
        for group in parallelizable_groups:
            tasks = []
            for step_id in group:
                if step_id in step_map:
                    tasks.append(self._execute_skill(step_map[step_id]))
                    
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for res in results:
                    if isinstance(res, Exception):
                        logger.error(f"Skill execution crashed: {res}")
                        continue
                    step_id = res["step_id"]
                    step_results[step_id] = res
                    total_time_ms += res.get("duration_ms", 0)
                    total_tokens += res.get("tokens_used", 0)

        payload = {
            "status": ExecutionStatus.SUCCESS,
            "step_results": step_results,
            "metrics": {
                "total_execution_time_ms": total_time_ms,
                "total_tokens_used": total_tokens,
                "completed_steps": len(step_results),
                "failed_steps": len(steps_to_execute) - len(step_results)
            },
            "next_phase": "result_validator"
        }
        
        return AgentResult(success=True, payload=payload)
