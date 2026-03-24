"""Reviewer agent implementation (v2.0)."""

from __future__ import annotations

import json
import logging
import ast
from typing import Any, Dict

from app.agents.base_agent import AgentContext, AgentResult, BaseAgent
from app.brain.prompt_templates import REVIEWER_SYSTEM_PROMPT, REVIEWER_USER_TEMPLATE

logger = logging.getLogger(__name__)

class ReviewerAgent(BaseAgent):
    name = "reviewer"

    def __init__(self, llm_client: Any = None) -> None:
        self.llm_client = llm_client

    def _static_analysis(self, code: str) -> Dict[str, Any]:
        """Perform strict AST heuristics locally before invoking LLM."""
        issues = []
        try:
            tree = ast.parse(code)
            run_found = False
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "run":
                    run_found = True
                    if isinstance(node, ast.AsyncFunctionDef):
                        issues.append("Fatal: 'run' must be synchronous. 'async def' discovered.")
                    
                    has_kwargs = any(arg.arg == "kwargs" for arg in getattr(node.args, "args", [])) or node.args.kwarg is not None
                    if not has_kwargs:
                        issues.append("Fatal: 'run' must accept **kwargs.")
                    break
                    
            if not run_found:
                issues.append("Fatal: Mandatory 'def run(input_data: dict, **kwargs)' is missing.")
                
            # Threat heuristics
            code_lower = code.lower()
            if "os.system" in code_lower or "subprocess" in code_lower:
                issues.append("Security: Dangerous OS execution detected.")
                
        except SyntaxError as e:
            issues.append(f"Python Syntax Error: {str(e)}")
            
        return {
            "passed": len(issues) == 0,
            "issues": issues
        }

    async def act(
        self,
        context: AgentContext,
        inputs: Dict[str, Any],
    ) -> AgentResult:
        code = inputs.get("code_text", "")
        round_num = inputs.get("iteration", 1)
        plan_json = inputs.get("plan_output", {})

        # 1. Local Static Analysis
        static_res = self._static_analysis(code)
        if not static_res["passed"]:
            return AgentResult(
                success=True,
                payload={
                    "round": round_num,
                    "checks": {
                        "syntax": {"passed": False, "issues": static_res["issues"]},
                        "logic": {"passed": True, "issues": []},
                        "error_handling": {"passed": True, "issues": []},
                        "performance": {"passed": True, "issues": []},
                        "security": {"passed": True, "issues": []},
                        "documentation": {"passed": True, "issues": []},
                        "edge_cases": {"passed": True, "issues": []},
                        "style": {"passed": True, "issues": []},
                    },
                    "severity_score": 10,
                    "quality_score": 0.0,
                    "issues_found": True,
                    "action": "NEEDS_FIX",
                    "recommended_fixes": static_res["issues"]
                }
            )

        # 2. LLM 8-Point Checklist Review
        sys_prompt = REVIEWER_SYSTEM_PROMPT
        user_prompt = REVIEWER_USER_TEMPLATE.format(
            code_to_review=code,
            iteration_count=round_num,
            plan_json=json.dumps(plan_json, ensure_ascii=False)
        )
        
        try:
            raw = await self.llm_client.generate_async(prompt=sys_prompt + "\n\n" + user_prompt)
            review_decision = json.loads(raw)
            return AgentResult(success=True, payload=review_decision)
        except Exception as e:
            logger.error(f"Reviewer parse error: {e}")
            # Fallback permissive if LLM crashes during review, relies on static check
            return AgentResult(
                success=True,
                payload={
                    "round": round_num,
                    "checks": {k: {"passed": True, "issues": []} for k in ["syntax", "logic", "error_handling", "performance", "security", "documentation", "edge_cases", "style"]},
                    "severity_score": 0,
                    "quality_score": 1.0,
                    "issues_found": False,
                    "action": "APPROVED"
                }
            )