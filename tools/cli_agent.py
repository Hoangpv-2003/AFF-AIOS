import sys
import os
import json
import uuid
import re
from pathlib import Path
from typing import Any, Dict, Optional

import io
import httpx
from dotenv import load_dotenv
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
from app.agents.manager import ManagerAgent
from app.agents.base_agent import AgentContext
from app.brain.prompt_templates import build_runtime_context
from app.api.v1.endpoints.agents import _execute_skill
load_dotenv()
# Cấu hình UTF-8 cho console Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Thêm root vào path để import app
sys.path.append(os.getcwd())

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


def _is_simple_direct_summary(intent_data: Dict[str, Any]) -> bool:
    action = str(intent_data.get("action_type", "")).lower()
    if action not in {"retrieve", "analyse"}:
        return False
    entities = intent_data.get("entities") or {}
    has_recipient = bool(str(entities.get("recipient", "")).strip())
    has_schedule = bool(str(entities.get("schedule_time", "")).strip())
    return not has_recipient and not has_schedule


def _direct_tavily_fetch(topic: str) -> Dict[str, Any]:
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        return {
            "status": "error",
            "summary": "Thiếu TAVILY_API_KEY.",
            "error_reason": "missing_tavily_api_key",
            "results": [],
        }
    query = topic.strip()
    if not query:
        return {
            "status": "error",
            "summary": "Thiếu chủ đề truy vấn.",
            "error_reason": "missing_topic",
            "results": [],
        }
    try:
        response = httpx.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "include_images": False,
                "search_depth": "advanced",
            },
            timeout=20.0,
        )
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results", []) if isinstance(payload, dict) else []
        return {
            "status": "success",
            "summary": f"Fetched {len(results)} results from Tavily.",
            "results": results,
        }
    except Exception as exc:
        return {
            "status": "error",
            "summary": "Không thể lấy dữ liệu realtime.",
            "error_reason": str(exc),
            "results": [],
        }


def _summarize_results_with_llm(
    llm_client: LoggingLLMClient,
    user_input: str,
    api_output: Dict[str, Any],
) -> str:
    prompt = (
        "Bạn là trợ lý phân tích dữ liệu. Tóm tắt ngắn gọn bằng tiếng Việt dựa trên dữ liệu thật bên dưới. "
        "Nêu rõ số liệu chính nếu có, không bịa số, không nhắc tên skill nội bộ.\n\n"
        f"Yêu cầu user: {user_input}\n\n"
        f"Du lieu API: {json.dumps(api_output, ensure_ascii=False)[:3500]}\n\n"
        "Trả về JSON duy nhất: {\"reply\": \"...\"}"
    )
    try:
        raw = str(llm_client.generate(prompt=prompt, response_format="json")).strip()
        parsed = json.loads(raw)
        if isinstance(parsed, dict) and parsed.get("reply"):
            return str(parsed.get("reply"))
        return raw
    except Exception as exc:
        return f"Không thể tổng hợp do lỗi LLM: {exc}"


def _wants_previous_report_context(user_text: str, intent_data: Dict[str, Any]) -> bool:
    action = str(intent_data.get("action_type", "")).lower()
    if action not in {"deliver", "pipeline", "mutate", "analyse"}:
        return False
    msg = user_text.lower()
    patterns = [
        r"vua roi",
        r"vừa rồi",
        r"bao cao vua",
        r"ket qua vua",
        r"previous",
        r"last report",
    ]
    return any(re.search(p, msg) for p in patterns)


def _extract_previous_delivery_context(execution_outputs: list[dict]) -> Dict[str, Any]:
    for item in reversed(execution_outputs):
        if not isinstance(item, dict):
            continue
        result = item.get("result")
        if not isinstance(result, dict):
            continue
        if str(result.get("status", "")).lower() != "success":
            continue
        context: Dict[str, Any] = {}
        for key in ("results", "summary", "summary_text", "images", "metrics", "report"):
            if key in result:
                context[key] = result[key]
        if context:
            return context
    return {}


def _tokenize_skill_text(text: str) -> set[str]:
    raw_tokens = re.findall(r"[a-z0-9]+", text.lower())
    stop = {
        "skill", "data", "info", "tool", "task", "the", "and", "for", "to",
        "bao", "cao", "thong", "ke", "du", "lieu",  # frequent VN split tokens
    }
    return {t for t in raw_tokens if len(t) > 2 and t not in stop}


def _skill_spec_tokens(skill_spec: Dict[str, Any]) -> set[str]:
    fields: list[str] = [
        str(skill_spec.get("skill_name", "")),
        str(skill_spec.get("skill_purpose", "")),
        str(skill_spec.get("coder_notes", "")),
    ]
    for key in skill_spec.get("input_keys") or []:
        fields.append(str(key))
    for key in skill_spec.get("output_keys") or []:
        fields.append(str(key))
    return _tokenize_skill_text(" ".join(fields))


def _skill_name_tokens(skill_name: str) -> set[str]:
    return _tokenize_skill_text(skill_name.replace("-", " ").replace("_", " "))


def _python_file_is_valid(file_path: Path) -> bool:
    try:
        source = file_path.read_text(encoding="utf-8")
        compile(source, str(file_path), "exec")
        return True
    except Exception:
        return False


def _python_code_is_valid(code: str) -> bool:
    try:
        compile(code, "<generated-skill>", "exec")
        return True
    except Exception:
        return False


def _build_skill_token_map(
    root: Path,
    available_static: list[str],
    available_dynamic: list[str],
) -> Dict[str, set[str]]:
    token_map: Dict[str, set[str]] = {}
    for name in list(available_static) + list(available_dynamic):
        base_tokens = _skill_name_tokens(name)
        source_tokens: set[str] = set()
        for folder in ["static", "dynamic"]:
            path = root / "app" / "skills" / folder / f"{name}.py"
            if path.exists() and _python_file_is_valid(path):
                try:
                    snippet = path.read_text(encoding="utf-8")[:5000]
                    source_tokens |= _tokenize_skill_text(snippet)
                except Exception:
                    pass
        token_map[name] = base_tokens | source_tokens
    return token_map


def _similarity_score(spec_tokens: set[str], cand_tokens: set[str]) -> float:
    if not spec_tokens or not cand_tokens:
        return 0.0
    inter = len(spec_tokens & cand_tokens)
    union = len(spec_tokens | cand_tokens)
    jaccard = (inter / union) if union else 0.0
    coverage = inter / max(1, len(spec_tokens))
    return max(jaccard, coverage)


def _auto_reuse_existing_skills(
    plan_data: Dict[str, Any],
    root: Path,
    available_static: list[str],
    available_dynamic: list[str],
    threshold: float,
) -> Dict[str, Any]:
    skills = plan_data.get("skills_to_create") or []
    if not isinstance(skills, list):
        return plan_data

    available = list(available_static) + list(available_dynamic)
    token_map = _build_skill_token_map(root, available_static, available_dynamic)
    rewritten: list[Dict[str, Any]] = []

    for raw in skills:
        if not isinstance(raw, dict):
            continue

        skill_name = str(raw.get("skill_name", "")).strip()
        if not skill_name:
            continue

        spec_tokens = _skill_spec_tokens(raw)
        best_name = ""
        best_score = 0.0

        for cand in available:
            cand_tokens = token_map.get(cand, _skill_name_tokens(cand))
            score = _similarity_score(spec_tokens, cand_tokens)

            # Prefer static reusable blocks when score is tied.
            if score > best_score or (
                score == best_score
                and cand in available_static
                and best_name not in available_static
            ):
                best_score = score
                best_name = cand

        # Auto-reuse threshold keeps behavior generic but safe.
        if best_name and best_score >= threshold:
            item = dict(raw)
            item["skill_name"] = best_name
            item["is_static"] = best_name in available_static
            rewritten.append(item)
        else:
            rewritten.append(dict(raw))

    # Remove duplicate entries after auto-reuse.
    dedup: Dict[str, Dict[str, Any]] = {}
    for item in rewritten:
        key = str(item.get("skill_name", "")).strip()
        if key and key not in dedup:
            dedup[key] = item

    plan_data["skills_to_create"] = list(dedup.values())
    return plan_data

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--real", action="store_true", help="Execute skills for real using sandbox")
    parser.add_argument("--prompt", type=str, help="Initial user objective to run non-interactively")
    parser.add_argument("--task-id", type=str, default=str(uuid.uuid4()), help="Custom task ID")
    parser.add_argument("--trace-id", type=str, default=str(uuid.uuid4()), help="Custom trace ID")
    parser.add_argument(
        "--planning-mode",
        type=str,
        default="standard",
        choices=["standard", "tot", "multi_persona"],
        help="Planner reasoning mode",
    )
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
    orchestrator = ManagerAgent(planner=planner, coder=coder, reviewer=reviewer, validator=validator)

    print(f"{BOLD}{GREEN}=== AAF-AIOS Terminal Pipeline Debugger ==={RESET}", flush=True)
    print(f"Models: Agent={settings.ollama_agent_model}, Coder={settings.ollama_coder_model}\n", flush=True)

    conversation_history = []
    previous_delivery_context: Dict[str, Any] = {}
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
        expected_goal = user_input

        # 0. Orchestrator preflight (state visibility)
        print(f"\n{BOLD}>>> [0/9] Orchestrator Preflight...{RESET}", flush=True)
        orchestrator_result = orchestrator.run(
            task_id=task_id,
            prompt=user_input,
            priority="standard",
        )
        print_log(
            "Orchestrator",
            f"Prompt: '{user_input}'",
            json.dumps(
                {
                    "final_state": orchestrator_result.final_state,
                    "reason_code": orchestrator_result.reason_code,
                    "transitions": orchestrator_result.transitions,
                    "execution_log": orchestrator_result.execution_log,
                },
                indent=2,
                ensure_ascii=False,
            ),
        )
        
        # 1. Intent Parser
        print(f"\n{BOLD}>>> [1/9] Intent Parsing...{RESET}", flush=True)
        res_intent = intent_parser.act(AgentContext(task_id=task_id, trace_id=trace_id, prompt=user_input), {"history": conversation_history})
        total_llm_calls += 1
        intent_data = res_intent.payload
        print_log("Intent Parser", f"User Message: '{user_input}'", json.dumps(intent_data, indent=2, ensure_ascii=False))
        use_previous_context = _wants_previous_report_context(user_input, intent_data)
        if use_previous_context and previous_delivery_context:
            print_log(
                "Context Carry",
                "Detected follow-up request for previous report",
                json.dumps(previous_delivery_context, ensure_ascii=False)[:1200],
            )
        
        # 1.5 Short-circuit for CHAT
        if intent_data.get("action_type") == "chat":
            print(f"{BOLD}>>> [1.5/9] Chat detected. Skipping pipeline...{RESET}", flush=True)
            exec_summary = "Đây là một cuộc hội thoại thông thường, không cần thực hiện skill bên ngoài."
            execution_outputs = []
            # Go directly to synthesis
        else:
            # 2. Planner
            print(f"{BOLD}>>> [2/9] Planning...{RESET}", flush=True)
            res_plan = planner.act(
                AgentContext(task_id=task_id, trace_id=trace_id, prompt=user_input),
                {
                    "history": conversation_history,
                    "intent_json": intent_data,
                    "runtime_context": runtime_context,
                    "planning_mode": args.planning_mode,
                },
            )
            total_llm_calls += 1
            plan_data = res_plan.payload.get("plan", {})
            if isinstance(plan_data, dict):
                static_skills = [f.stem for f in (root / "app" / "skills" / "static").glob("*.py")] if (root / "app" / "skills" / "static").exists() else []
                dynamic_skills = [f.stem for f in (root / "app" / "skills" / "dynamic").glob("*.py")] if (root / "app" / "skills" / "dynamic").exists() else []
                plan_data = _auto_reuse_existing_skills(
                    plan_data,
                    root,
                    static_skills,
                    dynamic_skills,
                    threshold=float(settings.cli_skill_reuse_score_threshold),
                )
            expected_goal = str(plan_data.get("task_summary") or user_input)
            print_log("Planner", f"Intent: {intent_data.get('action_type')}", json.dumps(plan_data, indent=2, ensure_ascii=False))

            if _is_simple_direct_summary(intent_data):
                topic = str((intent_data.get("entities") or {}).get("topic") or user_input)
                print(f"{BOLD}>>> [3/9] Direct API Fetch (Lightweight Flow)...{RESET}", flush=True)
                api_output = _direct_tavily_fetch(topic)
                execution_outputs = [{"skill": "direct-tavily", "result": api_output}]
                print_log(
                    "Direct API",
                    f"Topic: {topic}",
                    json.dumps(api_output, indent=2, ensure_ascii=False),
                )
                print(f"{BOLD}>>> [4/9] Direct LLM Summary (Lightweight Flow)...{RESET}", flush=True)
                direct_summary = _summarize_results_with_llm(llm_client, user_input, api_output)
                total_llm_calls += 1
                print_log("Direct Summary", "API results", direct_summary)
                exec_summary = direct_summary
            else:

                # 3. Skill Router
                print(f"{BOLD}>>> [3/9] Routing...{RESET}", flush=True)
            
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
                if not isinstance(skills_to_use, list):
                    skills_to_use = []

                # If router asks to build a skill that already exists, reuse it directly.
                build_after_reuse: list[str] = []
                for name in skills_to_build_names:
                    existing_path: Optional[Path] = None
                    for folder in ["static", "dynamic"]:
                        candidate = root / "app" / "skills" / folder / f"{name}.py"
                        if candidate.exists():
                            existing_path = candidate
                            break
                    exists = existing_path is not None and _python_file_is_valid(existing_path)
                    if exists:
                        if name not in skills_to_use:
                            skills_to_use.append(name)
                    else:
                        build_after_reuse.append(name)
                skills_to_build_names = build_after_reuse
            
                # Existence Failsafe: if Router thinks it exists but it doesn't, move to build
                validated_skills_to_use = []
                for s_name in skills_to_use:
                    exists = False
                    for folder in ["static", "dynamic"]:
                        candidate = root / "app" / "skills" / folder / f"{s_name}.py"
                        if candidate.exists() and _python_file_is_valid(candidate):
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
                coding_errors = []
                executed_skills.extend(validated_skills_to_use)

                # Build required skills
                for skill_spec in plan_data.get("skills_to_create", []):
                    name = skill_spec["skill_name"]
                    if name not in skills_to_build_names:
                        continue

                    print(f"{BOLD}>>> [5/9] Coding/Patching Skill: {name}...{RESET}", flush=True)
                    try:
                        res_coder = coder.act(
                            AgentContext(task_id=task_id, trace_id=trace_id, prompt=user_input),
                            {
                                "plan": plan_data,
                                "skill_name": name,
                                "runtime_context": runtime_context,
                                "total_llm_calls": total_llm_calls,
                            },
                        )
                        payload = res_coder.payload or {}
                        total_llm_calls = payload.get("total_llm_calls", total_llm_calls)
                        artifacts = payload.get("artifacts", {})
                        code_text = artifacts.get("generated_code", "")
                    except Exception as exc:
                        code_text = ""
                        artifacts = {"rationale": f"Coder error: {exc}"}
                        coding_errors.append(f"Coder failed for skill {name}: {exc}")
                        print(f"{RED}[ERROR]{RESET} Coder failed for '{name}': {exc}", flush=True)

                    if code_text:
                        if not _python_code_is_valid(code_text):
                            coding_errors.append(f"Generated invalid Python for skill {name}")
                            print(f"{RED}[ERROR]{RESET} Generated code for '{name}' is invalid Python. Skipping save.", flush=True)
                            print_log(
                                f"Coder (Skill: {name})",
                                f"Objective: {plan_data.get('task_summary')}",
                                "Generated code failed syntax validation and was skipped.",
                            )
                            continue

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

                    print_log(
                        f"Coder (Skill: {name})",
                        f"Objective: {plan_data.get('task_summary')}",
                        f"Rationale: {artifacts.get('rationale')}\n\nCode Preview: {len(code_text)} chars",
                    )

                # 5. Execution Phase (Sequential)
                exec_summaries = []
                execution_outputs = []
                if executed_skills:
                    ordered_by_plan: list[str] = []
                    for spec in plan_data.get("skills_to_create", []):
                        if not isinstance(spec, dict):
                            continue
                        s_name = str(spec.get("skill_name", "")).strip()
                        if s_name and s_name in executed_skills and s_name not in ordered_by_plan:
                            ordered_by_plan.append(s_name)
                    for s_name in executed_skills:
                        if s_name not in ordered_by_plan:
                            ordered_by_plan.append(s_name)
                    executed_skills = ordered_by_plan

                    accumulated_data = dict(intent_data.get("entities", {}))
                    if use_previous_context and previous_delivery_context:
                        for k, v in previous_delivery_context.items():
                            accumulated_data.setdefault(k, v)
                    for target in executed_skills:
                        if args.real:
                            print(f"{BOLD}>>> [6/9] EXECUTING REAL SKILL: {target}...{RESET}", flush=True)
                            try:
                                exec_res = _execute_skill(root, target, input_data=accumulated_data)
                            except Exception as exc:
                                exec_res = {
                                    "status": "error",
                                    "error_reason": str(exc),
                                    "skill_name": target,
                                }
                            execution_outputs.append({"skill": target, "result": exec_res})

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
                            execution_outputs.append({"skill": target, "result": {"status": "success", "summary": summary}})
                            print_log("Execution (Demo)", f"Target: {target}", summary, color=BLUE)

                    exec_summary = " | ".join(exec_summaries)
                else:
                    exec_summary = " | ".join(coding_errors) if coding_errors else "Execution halted: no runnable skills selected."
                    execution_outputs = []

        # 7. Result review gate before responding to user
        print(f"{BOLD}>>> [7/9] Reviewing Results...{RESET}", flush=True)
        validator_input = {
            "exec_summary": exec_summary,
            "outputs": execution_outputs,
        }
        validation = validator.act(
            AgentContext(task_id=task_id, trace_id=trace_id, prompt=user_input),
            {
                "original_request": user_input,
                "skill_output": json.dumps(validator_input, ensure_ascii=False),
                "expected_goal": expected_goal,
                "runtime_context": runtime_context,
                "history": conversation_history,
            },
        )
        total_llm_calls += 1
        validation_payload = validation.payload or {}
        print_log(
            "Result Validator",
            f"Goal: {expected_goal}",
            json.dumps(
                {
                    "success": validation.success,
                    "reason_code": validation.reason_code,
                    **(validation_payload if isinstance(validation_payload, dict) else {"payload": validation_payload}),
                },
                indent=2,
                ensure_ascii=False,
            ),
        )

        has_runtime_errors = any(
            str(item.get("result", {}).get("status", "")).lower() == "error"
            for item in execution_outputs
            if isinstance(item, dict)
        )

        is_valid = bool(validation_payload.get("isValid", False)) if isinstance(validation_payload, dict) else False
        if isinstance(validation_payload, dict) and "isValid" not in validation_payload:
            nested = validation_payload.get("result")
            nested_status = ""
            if isinstance(nested, dict):
                nested_status = str(nested.get("status", "")).lower()
            is_valid = (nested_status == "success") and not has_runtime_errors

        validation_code = str(validation_payload.get("result_code", "")) if isinstance(validation_payload, dict) else ""
        if validation.success and not is_valid:
            if validation_code == "REQUEST_REPLAN":
                retry_instruction = str(validation_payload.get("retry_instruction", ""))
                exec_summary = (
                    f"{exec_summary} | Validator requested replan: {retry_instruction}"
                    if retry_instruction else
                    f"{exec_summary} | Validator requested replan."
                )
            elif validation_code == "ESCALATE_TO_ERROR_HANDLER":
                detail = str(validation_payload.get("error_detail", "Không đủ dữ liệu để trả lời chắc chắn."))
                exec_summary = f"Validation escalation: {detail}"
            elif has_runtime_errors:
                exec_summary = f"Validation detected execution errors: {exec_summary}"
        
        # 8. Synthesis
        print(f"{BOLD}>>> [8/9] Synthesizing Final Answer...{RESET}", flush=True)
        from app.brain.prompt_templates import build_synthesizer_messages
        messages = build_synthesizer_messages(user_input, exec_summary)
        prompt = f"{messages[0]['content']}\n\n{messages[1]['content']}"
        reply = ""
        try:
            raw_reply = str(llm_client.generate(prompt=prompt, response_format="json")).strip()
            parsed_reply = json.loads(raw_reply)
            if isinstance(parsed_reply, dict):
                reply = str(parsed_reply.get("reply", "")).strip()
            if not reply:
                reply = raw_reply
        except Exception as exc:
            reply = f"Không thể tổng hợp phản hồi do lỗi LLM: {exc}. Kết quả thực thi: {exec_summary}"

        # Normalize accidental JSON-as-text replies.
        if reply.startswith("{") and reply.endswith("}"):
            try:
                candidate = json.loads(reply)
                if isinstance(candidate, dict) and candidate.get("reply"):
                    reply = str(candidate.get("reply"))
            except Exception:
                pass

        total_llm_calls += 1
        print_log("Synthesizer", f"Results: {exec_summary}", reply)

        fresh_context = _extract_previous_delivery_context(execution_outputs)
        if fresh_context:
            previous_delivery_context = fresh_context

        # Update History
        conversation_history.append({"role": "user", "content": user_input})
        conversation_history.append({"role": "assistant", "content": reply})

        print(f"\n{BOLD}{GREEN}Pipeline Completed! Total Calls: {total_llm_calls}{RESET}")
        print("-" * 50)

if __name__ == "__main__":
    main()
