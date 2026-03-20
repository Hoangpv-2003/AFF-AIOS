import sys
import os
import json
import uuid
from pathlib import Path
from typing import Any, Dict

import io
from dotenv import load_dotenv
load_dotenv()
# Cấu hình UTF-8 cho console Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Thêm root vào path để import app
sys.path.append(os.getcwd())

from app.core.config import get_settings
from app.api.dependencies import get_rag_service
from app.infrastructure.external_apis.ollama_client import OllamaLLMClient
from app.agents.intent_parser import IntentParserAgent
from app.agents.clarifier import ClarifierAgent
from app.brain.planner import PlannerAgent
from app.agents.skill_router import SkillRouterAgent
from app.agents.coder import CoderAgent
from app.agents.reviewer import ReviewerAgent
from app.agents.result_validator import ResultValidatorAgent
from app.agents.base_agent import AgentContext
from app.brain.prompt_templates import build_runtime_context
from app.api.v1.endpoints.agents import _execute_skill

# ANSI Colors
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

class LoggingLLMClient(OllamaLLMClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_raw = "No response yet"

    def generate(self, prompt: str, **kwargs) -> str:
        res = super().generate(prompt, **kwargs)
        self.last_raw = res
        return res

def print_log(title: str, input_data: str, output_data: str, color=BLUE):
    print(f"\n{BOLD}{color}>>> STEP: {title}{RESET}", flush=True)
    print(f"{YELLOW}[INPUT]{RESET} {input_data}", flush=True)
    print(f"{GREEN}[OUTPUT]{RESET} {output_data}", flush=True)
    print(f"{color}{'-'*20}{RESET}", flush=True)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--real", action="store_true", help="Execute skills for real using sandbox")
    parser.add_argument("--prompt", type=str, help="Initial user objective to run non-interactively")
    parser.add_argument("--task-id", type=str, default=str(uuid.uuid4()), help="Custom task ID")
    parser.add_argument("--trace-id", type=str, default=str(uuid.uuid4()), help="Custom trace ID")
    args = parser.parse_args()
    
    settings = get_settings()
    root = Path(os.getcwd())
    # Use LoggingLLMClient to capture raw outputs
    llm_client = LoggingLLMClient(
        base_url=settings.ollama_base_url,
        primary_model=settings.ollama_chat_model,
        fallback_models=[]
    )
    agent_llm = LoggingLLMClient(
        base_url=settings.ollama_base_url, 
        primary_model=settings.ollama_agent_model,
        fallback_models=[]
    )
    coder_llm = LoggingLLMClient(
        base_url=settings.ollama_base_url, 
        primary_model=settings.ollama_coder_model,
        fallback_models=[]
    )
    
    # Init Agents
    rag_service = get_rag_service()
    intent_parser = IntentParserAgent(llm_client=agent_llm)
    clarifier = ClarifierAgent(llm_client=agent_llm)
    planner = PlannerAgent(llm_client=agent_llm)
    skill_router = SkillRouterAgent(llm_client=agent_llm)
    reviewer = ReviewerAgent(llm_client=agent_llm)
    coder = CoderAgent(llm_client=coder_llm, reviewer=reviewer, rag_service=rag_service)
    validator = ResultValidatorAgent(llm_client=agent_llm)

    print(f"{BOLD}{GREEN}=== AAF-AIOS Terminal Pipeline Debugger ==={RESET}", flush=True)
    print(f"Models: Agent={settings.ollama_agent_model}, Coder={settings.ollama_coder_model}\n", flush=True)

    conversation_history = []
    while True:
        if args.prompt:
            user_input = args.prompt
            print(f"{BOLD}User Objective (from --prompt): {RESET}{user_input}", flush=True)
        else:
            user_input = input(f"{BOLD}User Objective (or 'exit'): {RESET}")
            
        if user_input.lower() in ["exit", "quit"]:
            break

        # Clear prompt after first use if it was provided
        if args.prompt:
            args.prompt = "exit" # Exit loop after one run
        task_id = args.task_id
        trace_id = args.trace_id
        total_llm_calls = 0
        runtime_context = build_runtime_context(history=conversation_history)
        
        # 1. Intent Parser
        print(f"\n{BOLD}>>> [1/7] Intent Parsing...{RESET}", flush=True)
        res_intent = intent_parser.act(AgentContext(task_id=task_id, trace_id=trace_id, prompt=user_input), {"history": conversation_history})
        total_llm_calls += 1
        intent_data = res_intent.payload
        print_log("Intent Parser", f"User Message: '{user_input}'", json.dumps(intent_data, indent=2, ensure_ascii=False))

        # 2. Planner
        print(f"{BOLD}>>> [2/7] Planning...{RESET}", flush=True)
        res_plan = planner.act(AgentContext(task_id=task_id, trace_id=trace_id, prompt=user_input), {"history": conversation_history, "intent_json": intent_data, "runtime_context": runtime_context})
        total_llm_calls += 1
        plan_data = res_plan.payload.get("plan", {})
        print_log("Planner", f"Intent: {intent_data.get('action_type')}", json.dumps(plan_data, indent=2, ensure_ascii=False))

        # 3. Skill Router
        print(f"{BOLD}>>> [3/7] Routing...{RESET}", flush=True)
        
        # Discover available skills
        available_skills_list = []
        for folder in ["static", "dynamic"]:
            path = root / "app" / "skills" / folder
            if path.exists():
                available_skills_list.extend([f.stem for f in path.glob("*.py")])
        
        res_route = skill_router.act(
            AgentContext(task_id=task_id, trace_id=trace_id, prompt=user_input), 
            {
                "history": conversation_history, 
                "plan_json": json.dumps(plan_data, ensure_ascii=False), 
                "available_skills": ", ".join(available_skills_list), 
                "data_sources": "Tavily, RAG",
                "runtime_context": runtime_context
            }
        )
        total_llm_calls += 1
        router_data = res_route.payload
        print_log("Skill Router", f"Plan Summary: {plan_data.get('task_summary')}", json.dumps(router_data, indent=2, ensure_ascii=False))
        # 4. Routing Decision & Execution Preparation
        route_type = str(router_data.get("route", "")).upper()
        raw_build_list = router_data.get("skills_to_build", [])
        skills_to_build_names = []
        if isinstance(raw_build_list, list):
            for item in raw_build_list:
                if isinstance(item, dict):
                    skills_to_build_names.append(item.get("skill_name", ""))
                else:
                    skills_to_build_names.append(str(item))
        skills_to_use = router_data.get("skills_to_use", [])
        
        # Existence Failsafe: if Router thinks it exists but it doesn't, move to build
        validated_skills_to_use = []
        for s_name in skills_to_use:
            exists = False
            for folder in ["static", "dynamic"]:
                if (root / "app" / "skills" / folder / f"{s_name}.py").exists():
                    exists = True
                    break
            if exists:
                validated_skills_to_use.append(s_name)
            else:
                print(f"{YELLOW}[WARNING]{RESET} Router hallucinated skill '{s_name}'. Adding to build list.", flush=True)
                if s_name not in skills_to_build_names:
                    skills_to_build_names.append(s_name)

        # 4.1 Realtime Fetcher Gate
        if "REALTIME" in route_type:
            queries = router_data.get("realtime_queries", [])
            # Ideally call REALTIME_FETCHER here, for now simulate injection
            runtime_context += f"\n[REALTIME_DATA]: Results for {queries} fetched from Tavily."
            print_log("Realtime Fetcher", f"Queries: {queries}", "Data injected into RUNTIME_CONTEXT.", color=YELLOW)

        # 4.2 Coder Phase
        executed_skills = []
        # Add existing validated skills first
        executed_skills.extend(validated_skills_to_use)
        
        # Build required skills
        # We need to iterate over plan_data['skills_to_create'] to get full specs for Coder
        for skill_spec in plan_data.get("skills_to_create", []):
            name = skill_spec["skill_name"]
            if name not in skills_to_build_names:
                continue
                
            print(f"{BOLD}>>> [5/7] Coding/Patching Skill: {name}...{RESET}", flush=True)
            res_coder = coder.act(
                AgentContext(task_id=task_id, trace_id=trace_id, prompt=user_input),
                {
                    "plan": plan_data,
                    "skill_name": name,
                    "runtime_context": runtime_context,
                    "total_llm_calls": total_llm_calls
                }
            )
            total_llm_calls = res_coder.payload.get("total_llm_calls", total_llm_calls)
            artifacts = res_coder.payload.get("artifacts", {})
            code_text = artifacts.get("generated_code", "")
            
            if code_text:
                # PERSIST generated code
                is_static = skill_spec.get("is_static", False)
                folder = "static" if is_static else "dynamic"
                save_path = root / "app" / "skills" / folder / f"{name}.py"
                print(f"{YELLOW}[DEBUG]{RESET} Saving skill '{name}' to {save_path.absolute()}", flush=True)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                save_path.write_text(code_text, encoding="utf-8")
                if save_path.exists():
                    print(f"{GREEN}[DEBUG]{RESET} Successfully saved {save_path.name} ({len(code_text)} bytes)", flush=True)
                else:
                    print(f"{RED}[DEBUG]{RESET} Failed to save skill to disk!", flush=True)
                
                if name not in executed_skills:
                    executed_skills.append(name)
                
            print_log(f"Coder (Skill: {name})", f"Objective: {plan_data.get('task_summary')}", f"Rationale: {artifacts.get('rationale')}\n\nCode Preview: {len(code_text)} chars")

        # 5. Execution Phase (Sequential)
        exec_summaries = []
        if executed_skills:
            accumulated_data = dict(intent_data.get("entities", {}))
            for target in executed_skills:
                if args.real:
                    print(f"{BOLD}>>> [6/7] EXECUTING REAL SKILL: {target}...{RESET}", flush=True)
                    exec_res = _execute_skill(root, target, **accumulated_data)
                    
                    if exec_res.get("status") == "success":
                        accumulated_data.update(exec_res)
                        summary = exec_res.get("summary") or exec_res.get("reply") or f"Executed {target} successfully."
                    else:
                        summary = f"Error in {target}: {exec_res.get('error_reason')}"
                        print(f"{RED}[ERROR]{RESET} {exec_res.get('error_reason')}", flush=True)
                    
                    exec_summaries.append(summary)
                    print_log("Real Execution", f"Target: {target}", json.dumps(exec_res, indent=2, ensure_ascii=False), color=BLUE)
                else:
                    summary = f"Successfully fetched and processed data for '{target}' (Demo Mode)."
                    exec_summaries.append(summary)
                    print_log("Execution (Demo)", f"Target: {target}", summary, color=BLUE)
            
            exec_summary = " | ".join(exec_summaries)
        else:
            exec_summary = "No specific skills were executed."
        
        # 6. Synthesis
        print(f"{BOLD}>>> [7/7] Synthesizing Final Answer...{RESET}", flush=True)
        from app.brain.prompt_templates import build_synthesizer_messages
        messages = build_synthesizer_messages(user_input, exec_summary)
        prompt = f"{messages[0]['content']}\n\n{messages[1]['content']}"
        try:
            reply = str(llm_client.generate(prompt=prompt)).strip()
        except:
            reply = "Đã thực hiện xong."
        total_llm_calls += 1
        print_log("Synthesizer", f"Results: {exec_summary}", reply)

        # Update History
        conversation_history.append({"role": "user", "content": user_input})
        conversation_history.append({"role": "assistant", "content": reply})

        print(f"\n{BOLD}{GREEN}Pipeline Completed! Total Calls: {total_llm_calls}{RESET}")
        print("-" * 50)

if __name__ == "__main__":
    main()
