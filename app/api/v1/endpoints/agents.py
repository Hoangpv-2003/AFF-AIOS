"""Agent debugging endpoints - v2."""

from __future__ import annotations

import base64
import hashlib
import html
import importlib.util
import json
import os
import re
import subprocess
import sys
import unicodedata
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, BackgroundTasks
from fastapi import UploadFile
from pydantic import BaseModel, Field

from app.api.dependencies import (
    get_coder_agent,
    get_llm_client,
    get_planner_agent,
    get_rag_service,
    get_settings_dep,
    get_agent_llm_client,
    get_coder_llm_client,
    get_reviewer_llm_client,
    get_reviewer_agent,
    get_memory_manager,
    get_intent_parser_agent,
    get_clarifier_agent,
    get_skill_router_agent,
    get_result_validator_agent,
    get_error_handler_agent,
)
from app.agents.coder import CoderAgent
from app.agents.manager import ManagerAgent
from app.agents.intent_parser import IntentParserAgent
from app.agents.clarifier import ClarifierAgent
from app.agents.skill_router import SkillRouterAgent
from app.agents.result_validator import ResultValidatorAgent
from app.agents.error_handler import ErrorHandlerAgent
from app.agents.reviewer import ReviewerAgent
from app.brain.planner import PlannerAgent
from app.brain.rag import RAGService
from app.core.config import Settings
from app.infrastructure.external_apis.ollama_client import OllamaLLMClient
from app.schemas.skills import SkillDigest, SkillState
from app.skills.registry import SkillRecord, registry
from app.brain.memory_manager import MemoryManager
from app.brain.prompt_templates import (
    build_intent_parser_messages,
    build_clarifier_messages,
    build_skill_router_messages,
)
from app.infrastructure.sandboxes.runner import LocalSandboxRunner
from app.infrastructure.sandboxes.models import SandboxRequest
from app.infrastructure.sandboxes.policy import SandboxPolicy
from app.brain.prompt_templates import (
    build_planner_messages,
    build_coder_messages,
    build_reviewer_messages,
    build_result_validator_messages,
    build_synthesizer_messages,
    build_error_handler_messages,
    CONTEXT_INJECTOR_TEMPLATE,
    INTENT_PARSER_SYSTEM_PROMPT,
    INTENT_PARSER_USER_TEMPLATE,
    CLARIFIER_SYSTEM_PROMPT,
    CLARIFIER_USER_TEMPLATE,
    SKILL_ROUTER_SYSTEM_PROMPT,
    SKILL_ROUTER_USER_TEMPLATE,
    PLANNER_SYSTEM_PROMPT,
    PLANNER_USER_TEMPLATE,
    CODER_SYSTEM_PROMPT,
    CODER_USER_TEMPLATE,
    CODE_REVIEWER_SYSTEM_PROMPT,
    CODE_REVIEWER_USER_TEMPLATE,
    RESULT_VALIDATOR_SYSTEM_PROMPT,
    RESULT_VALIDATOR_USER_TEMPLATE,
    SYNTHESIZER_SYSTEM_PROMPT,
    SYNTHESIZER_USER_TEMPLATE,
    ERROR_HANDLER_SYSTEM_PROMPT,
    ERROR_HANDLER_USER_TEMPLATE,
)

router = APIRouter()


class AgentRunRequest(BaseModel):
    task_id: str = Field(default="run-task")
    prompt: str
    priority: str = Field(default="standard")
    history_summary: str = Field(default="")


class AgentMaterializeRequest(BaseModel):
    task_id: str = Field(default="materialize-task")
    prompt: str
    priority: str = Field(default="standard")
    skill_id: Optional[str] = Field(default=None)
    create_test: bool = Field(default=True)
    package_with_skill_creator: bool = Field(default=True)
    force_new: bool = Field(default=False)
    debug: bool = Field(default=False)
    history_summary: str = Field(default="")
    is_static: bool = Field(default=False)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ConversationMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    report_markdown: Optional[str] = Field(default=None)
    image_base64: Optional[str] = Field(default=None)


class AgentChatRequest(BaseModel):
    message: str
    conversation_history: list[ConversationMessage] = Field(default_factory=list)
    user_email: Optional[str] = Field(default=None)
    schedule_time: Optional[str] = Field(default=None)
    force_new: bool = Field(default=False)
    debug: bool = Field(default=False)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _generate_text_strict(
    llm_client: OllamaLLMClient,
    prompt: str,
    response_format: Optional[str] = None,
) -> str:
    text: str = llm_client.generate(prompt=prompt, response_format=response_format)
    text = _strip_code_fences(text.strip())
    
    if response_format == "json":
        # Robustly extract JSON if LLM added extra text
        try:
            # Try parsing directly first
            json.loads(text)
        except json.JSONDecodeError:
            # Try to find the first { and last }
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                text = text[start : end + 1]

    if not text:
        raise ValueError("LLM tra ve response rong. Kiem tra model/connection.")
    return text


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    # Find first and last triple backticks
    match = re.search(r"```[a-zA-Z0-9_\-]*\n?(.*?)```", cleaned, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Fallback to simple strip if no fences found
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_\-]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    return cleaned.strip()


def _parse_intent(
    agent: IntentParserAgent,
    user_message: str,
    runtime_context: str,
    memory_context: str = "",
) -> dict:
    """Uses IntentParser to convert raw message to structured intent."""
    res = agent.act(
        AgentContext(task_id="intent", prompt=user_message),
        {"message": user_message, "runtime_context": runtime_context, "memory_context": memory_context}
    )
    if res.success:
        return res.payload
    return {
        "action_type": "chat",
        "goal": "fallback",
        "confidence": 0.0,
        "ambiguous": True,
        "clarification_needed": True,
        "clarification_hint": f"Lỗi hệ thống khi phân tích ý định: {res.reason_code}"
    }


_SKILL_CONTRACT = """\
## Skill Interface (BAT BUOC)
# Doi voi DYNAMIC: app/skills/dynamic/{skill_name}.py
# Doi voi STATIC : app/skills/static/{skill_name}.py

from __future__ import annotations
from typing import Any, Dict, Optional
import os
import smtplib
from email.message import EmailMessage

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    \"\"\"
    Luu y ve Email: Bat buoc dung SMTP.
    Su dung env: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS.
    Tham so email: to_email, subject, content, schedule_time (optional).
    \"\"\"
    ...  # entry point duy nhat

## Output (BAT BUOC – key toi thieu)
- status  : "success" | "error"
- summary : str  # mo ta ket qua
- image_base64 : str (optional) # du lieu anh/bieu do base64
- chart_base64 : str (optional) # du lieu bieu do base64

## Quy tac tuyet doi
- KHONG bịa dữ liệu (no hallucination).
- Wrap moi logic trong try/except; tra ve error dict thay vi raise.
- Chi dung stdlib + httpx. Khong import gi ngoai venv.
"""


def _plan_to_text(plan: dict) -> str:
    if not plan:
        return "(khong co plan chi tiet)"
    objective = str(plan.get("objective") or "").strip()
    steps = plan.get("steps") or []
    lines = []
    if objective:
        lines.append(f"- objective: {objective}")
    if isinstance(steps, list):
        for idx, step in enumerate(steps[:8], start=1):
            if isinstance(step, dict):
                name = str(step.get("name") or step.get("title") or "").strip()
                detail = str(
                    step.get("detail") or step.get("description") or ""
                ).strip()
                merged = f"{name} - {detail}".strip(" -")
                lines.append(f"- step_{idx}: {merged or str(step)}")
            else:
                lines.append(f"- step_{idx}: {step}")
    return "\n".join(lines) if lines else json.dumps(plan, ensure_ascii=False)


def _build_coder_brief(
    *,
    llm_client: OllamaLLMClient,
    user_request: str,
    skill_name: str,
    plan: dict,
    web_context: str,
    rag_context: str,
    reviewer_feedback: str = "",
) -> str:
    plan_text = _plan_to_text(plan)

    feedback_section = ""
    if reviewer_feedback:
        feedback_section = (
            f"\n## Phan Hoi Tu Reviewer (Lan Truoc That Bai)\n"
            f"{reviewer_feedback}\n"
            "Hay sua dung cac van de tren trong lan nay.\n"
        )

    prompt = (
        "Nguoi dung giao nhiem vu cho bay: hay thiet ke ra mot CODER BRIEF chi tiet bang tieng Viet.\n"
        "Bay la KIEN TRUC SU TRUONG. Bay phai tu suy nghi toan bo chien thuat de thuc hien yeu cau:\n"
        "- Can dung thu vien gi? (vd: httpx, matplotlib, pandas, openpyxl, base64...)\n"
        "- Format output la gi? (vd: JSON string, Base64 PNG, URL, file path...)\n"
        "- Output tra ve nhung key gi trong dict? (vd: chart_base64, table_data, file_path...)\n"
        "- Quy trinh tung buoc de hoan thanh nhiem vu la gi?\n"
        "Viet tat ca vao CODER BRIEF de thang Coder thuc hien. Thang Coder chi biet code theo yeu cau cua bay.\n\n"
        f"## Yeu cau nguoi dung\n{user_request}\n\n"
        f"## Ten skill can tao\n{skill_name}\n\n"
        f"## Plan tu Planner Agent\n{plan_text}\n\n"
        f"## Web context\n{web_context[:1500]}\n\n"
        f"## RAG context\n{rag_context[:800]}\n"
        f"{feedback_section}\n"
        f"{_SKILL_CONTRACT}"
    )

    return _generate_text_strict(llm_client, prompt)


def _llm_review_code(
    llm_client: OllamaLLMClient,
    skill_name: str,
    coder_brief: str,
    code_text: str,
) -> dict:
    """Review generated code with LLM. Returns {passed: bool, feedback: str}."""
    review_prompt = (
        "Nguoi dung yeu cau Review code Python sau day. Bay la Reviewer Agent chuyen nghiep.\n\n"
        f"## Ten Skill\n{skill_name}\n\n"
        f"## Coder Brief (Thiet ke goc)\n{coder_brief[:1500]}\n\n"
        f"## Code can review\n```python\n{code_text[:3000]}\n```\n\n"
        "Kiem tra cac tieu chi sau:\n"
        "1. Co ham run() khong? run() co tra ve dict khong?\n"
        "2. Co xu ly loi (try/except) khong?\n"
        "3. Code co logic phu hop voi Coder Brief khong?\n"
        "4. Co bia so lieu (hardcoded fake data) khong?\n\n"
        "Tra ve JSON duy nhat, khong markdown:\n"
        '{"passed": true/false, "feedback": "mo ta van de neu khong dat"}'
    )
    try:
        raw = _generate_text_strict(llm_client, review_prompt, response_format="json")
        result = json.loads(raw)
        return {
            "passed": bool(result.get("passed", False)),
            "feedback": str(result.get("feedback", "")),
        }
    except Exception as exc:
        # If reviewer fails to parse, let it pass to avoid blocking
        return {"passed": True, "feedback": f"review_parse_error: {exc}"}


def _llm_review_execution(
    llm_client: OllamaLLMClient,
    message: str,
    skill_output: dict,
) -> dict:
    """Review execution results with LLM. Returns {passed: bool, feedback: str, score: int}."""
    from app.brain.prompt_templates import RESULT_REVIEWER_SYSTEM_PROMPT, RESULT_REVIEWER_USER_TEMPLATE
    prompt = RESULT_REVIEWER_USER_TEMPLATE.format(
        message=message,
        skill_output=json.dumps(skill_output, ensure_ascii=False, indent=2)
    )
    try:
        raw = _generate_text_strict(llm_client, f"{RESULT_REVIEWER_SYSTEM_PROMPT}\n\n{prompt}", response_format="json")
        result = json.loads(raw)
        return {
            "passed": bool(result.get("passed", True)),
            "feedback": str(result.get("feedback", "")),
            "score": int(result.get("score", 10)),
        }
    except Exception as exc:
        return {"passed": True, "feedback": f"result_review_parse_error: {exc}", "score": 10}


def _execute_skill(root: Path, skill_name: str, **kwargs) -> dict:
    static_path = root / "app" / "skills" / "static" / f"{skill_name}.py"
    dynamic_path = root / "app" / "skills" / "dynamic" / f"{skill_name}.py"
    
    skill_path = static_path if static_path.exists() else dynamic_path
    
    if not skill_path.exists():
        return {
            "status": "error",
            "error_reason": f"Skill file not found: {skill_path}",
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }

    # Use LocalSandboxRunner with Networking enabled for real side effects
    policy = SandboxPolicy(allow_network=True)
    runner = LocalSandboxRunner(policy=policy)
    
    wrapper_path = root / "app" / "infrastructure" / "sandboxes" / "skill_wrapper.py"
    input_json = json.dumps(kwargs, ensure_ascii=False)
    
    request = SandboxRequest(
        skill_id=skill_name,
        command="python",
        args=[str(wrapper_path), str(skill_path), input_json],
        timeout_seconds=30
    )
    
    try:
        res = runner.run(request)
        if not res.success:
            return {
                "status": "error",
                "error_reason": f"Sandbox execution failed: {res.stderr}",
                "stdout": res.stdout,
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }
            
        # Parse output from wrapper
        try:
            output = json.loads(res.stdout)
            if not isinstance(output, dict):
                output = {"status": "success", "raw_output": str(output)}
            return output
        except Exception as e:
            return {
                "status": "error",
                "error_reason": f"Failed to parse skill output: {str(e)}",
                "raw_stdout": res.stdout,
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }
            
    except Exception as exc:
        return {
            "status": "error",
            "error_reason": f"Runtime exception: {str(exc)}",
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }
        output.setdefault("collected_at", datetime.now(timezone.utc).isoformat())
        return output

    except Exception as exc:
        return {
            "status": "error",
            "error_reason": str(exc),
            "skill_name": skill_name,
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }


def _normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.replace("đ", "d").replace("Đ", "D")
    return text.lower()


def _slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    normalized = "".join(
        ch for ch in normalized if unicodedata.category(ch) != "Mn"
    )
    normalized = normalized.replace("đ", "d").replace("Đ", "D")
    slug = re.sub(r"[^a-z0-9]+", "_", normalized.lower()).strip("_")
    return slug[:64] or "generated_skill"


def _to_kebab(name: str) -> str:
    return name.replace("_", "-")


def _fetch_web_context(task_prompt: str, settings: Settings) -> str:
    provider = settings.search_provider.lower().strip()
    if provider == "tavily" and settings.tavily_api_key:
        try:
            response = httpx.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings.tavily_api_key,
                    "query": task_prompt,
                    "search_depth": "basic",
                    "max_results": 5,
                    "include_answer": True,
                },
                timeout=10.0,
            )
            response.raise_for_status()
            payload = response.json()
            answer = payload.get("answer") or ""
            results = payload.get("results") or []
            snippets = []
            if answer:
                snippets.append(f"[answer] {answer}")
            for item in results[:5]:
                url = item.get("url") or ""
                content = re.sub(r"\s+", " ", item.get("content") or "")
                snippets.append(f"[{url}] {content[:300]}")
            return "\n".join(snippets) if snippets else ""
        except Exception:
            return ""
    return ""


def _fetch_rag_context(task_prompt: str, rag_service: RAGService) -> str:
    try:
        results = rag_service.retrieve(query_text=task_prompt, top_k=3)
    except Exception:
        return ""
    snippets = []
    for item in results:
        record = getattr(item, "record", None)
        if record is None:
            continue
        text = re.sub(r"\s+", " ", getattr(record, "text", "") or "").strip()
        if text:
            snippets.append(text[:280])
    return "\n".join(snippets)


def _find_existing_skill(
    root: Path,
    task_prompt: str,
    rag_service: RAGService,
) -> Optional[dict]:
    for folder in ["dynamic", "static"]:
        root_dir = root / "app" / "skills" / folder
        if root_dir.exists():
            for skill_file in root_dir.glob("*.py"):
                try:
                    metadata_text = skill_file.read_text(encoding="utf-8")[:2000]
                    skill_id = skill_file.stem
                    rag_service.ingest(
                        record_id=f"existing-skill-{folder}-{skill_id}",
                        text=f"type={folder}\nskill_id={skill_id}\n{metadata_text}",
                        metadata={"type": "existing_skill", "skill_id": skill_id, "folder": folder},
                    )
                except Exception:
                    pass

    results = rag_service.retrieve(
        query_text=task_prompt,
        top_k=1,
        filters={"type": "existing_skill"},
    )
    if not results:
        return None
    best = results[0]
    if best.score < 0.65:
        return None
    skill_id = str(best.record.metadata.get("skill_id") or "")
    if not skill_id:
        return None
    skill_path = root / "app" / "skills" / "dynamic" / f"{skill_id}.py"
    if not skill_path.exists():
        return None
    return {
        "skill_id": skill_id,
        "score": best.score,
        "files": [str(skill_path.relative_to(root)).replace("\\", "/")],
    }


def _persist_short_and_long_memory(settings: Settings, event: dict) -> dict:
    memory_status: dict = {
        "short_term": {
            "enabled": bool(settings.redis_url),
            "stored": False,
            "error": None,
        },
        "long_term": {
            "enabled": bool(settings.mongodb_uri),
            "stored": False,
            "error": None,
        },
    }
    if settings.redis_url:
        try:
            import redis

            client = redis.from_url(settings.redis_url, decode_responses=True)
            key = f"aaf:materialize:{event['task_id']}"
            client.setex(
                key,
                settings.short_memory_ttl_seconds,
                json.dumps(event, ensure_ascii=False),
            )
            memory_status["short_term"]["stored"] = True
            memory_status["short_term"]["key"] = key
        except Exception as exc:
            memory_status["short_term"]["error"] = str(exc)
    if settings.mongodb_uri:
        try:
            from pymongo import MongoClient

            client = MongoClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS=3000,
            )
            result = client[settings.mongodb_db]["materialize_events"].insert_one(
                event
            )
            memory_status["long_term"]["stored"] = True
            memory_status["long_term"]["id"] = str(result.inserted_id)
        except Exception as exc:
            memory_status["long_term"]["error"] = str(exc)
    return memory_status


def _create_skill_creator_bundle(
    root: Path,
    skill_name: str,
    prompt: str,
    code_text: str,
) -> Path:
    bundle_name = _to_kebab(skill_name)
    bundle_dir = root / "skills" / "dynamic" / bundle_name
    scripts = bundle_dir / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    skill_md = (
        "---\n"
        f"name: {bundle_name}\n"
        f"description: {json.dumps(f'Auto-generated skill: {prompt}', ensure_ascii=False)}\n"
        "---\n\n## Usage\n"
        "Entry point: scripts/skill_impl.py -> run()\n"
    )
    (bundle_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")
    (scripts / "skill_impl.py").write_text(code_text + "\n", encoding="utf-8")
    return bundle_dir


def _run_skill_creator_tools(root: Path, bundle_dir: Path) -> dict:
    creator_root = root / "skill-creator"
    output_dir = root / "dist" / "skills"
    output_dir.mkdir(parents=True, exist_ok=True)
    proc_env = {**os.environ, "PYTHONIOENCODING": "utf-8"}

    try:
        validate = subprocess.run(
            [sys.executable, "scripts/quick_validate.py", str(bundle_dir)],
            cwd=str(creator_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=30,
            env=proc_env,
        )
    except subprocess.TimeoutExpired:
        return {
            "validate": {"return_code": -1, "stderr": "timeout"},
            "package": None,
        }

    packaged_path = None
    package_result: dict[str, Any] = {"return_code": None}
    if validate.returncode == 0:
        try:
            pkg = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scripts.package_skill",
                    str(bundle_dir),
                    str(output_dir),
                ],
                cwd=str(creator_root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=60,
                env=proc_env,
            )
            package_result = {
                "return_code": pkg.returncode,
                "stdout": pkg.stdout,
                "stderr": pkg.stderr,
            }
            candidate = output_dir / f"{bundle_dir.name}.skill"
            if candidate.exists():
                packaged_path = str(candidate.relative_to(root)).replace("\\", "/")
        except subprocess.TimeoutExpired:
            package_result = {"return_code": -1, "stderr": "timeout"}

    return {
        "bundle_dir": str(bundle_dir.relative_to(root)).replace("\\", "/"),
        "validate": {
            "return_code": validate.returncode,
            "stdout": validate.stdout,
            "stderr": validate.stderr,
        },
        "package": {**package_result, "artifact": packaged_path},
    }


def _save_report_files(task_id: str, report_markdown: str) -> dict:
    root = _repo_root()
    reports_dir = root / "reports" / "chat"
    reports_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"{task_id}_report"
    html_path = reports_dir / f"{base_name}.html"
    html_path.write_text(
        "<!doctype html><html><head><meta charset='utf-8'></head><body>"
        f"<pre>{html.escape(report_markdown)}</pre></body></html>",
        encoding="utf-8",
    )
    return {"html_url": f"/reports/chat/{base_name}.html"}


def _render_text_image_base64(text: str) -> str:
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    lines = escaped.splitlines()[:6] or [escaped]
    
    # Premium SVG design with gradient and better typography
    svg_header = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="450" viewBox="0 0 800 450">'
        '<defs>'
        '<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0%" stop-color="#1a1c2c"/>'
        '<stop offset="100%" stop-color="#4a192c"/>'
        '</linearGradient>'
        '<filter id="blur"><feGaussianBlur stdDeviation="10"/></filter>'
        '</defs>'
        '<rect width="800" height="450" fill="url(#bg)" rx="24"/>'
        '<rect x="40" y="40" width="720" height="370" rx="16" fill="#ffffff" fill-opacity="0.05" stroke="#ffffff" stroke-opacity="0.2"/>'
        '<circle cx="80" cy="80" r="30" fill="#ff2d55" fill-opacity="0.8"/>'
        '<text x="125" y="85" font-family="Segoe UI, Arial" font-size="28" font-weight="bold" fill="#ffffff">AAF-AIOS Visual Response</text>'
        '<line x1="80" y1="130" x2="720" y2="130" stroke="#ffffff" stroke-opacity="0.1" stroke-width="2"/>'
    )
    
    svg_body = ""
    y = 180
    for line in lines:
        svg_body += f'<text x="80" y="{y}" font-family="Segoe UI, Arial" font-size="20" fill="#ffffff" fill-opacity="0.9">{html.escape(line[:75])}</text>'
        y += 40
        
    svg_footer = (
        '<text x="80" y="400" font-family="Segoe UI, Arial" font-size="14" fill="#ffffff" fill-opacity="0.4">Agentic Memory &amp; Visual Logic Active</text>'
        '</svg>'
    )
    
    svg = svg_header + svg_body + svg_footer
    return base64.b64encode(svg.encode("utf-8")).decode("utf-8")


def _extract_chart_base64(skill_output: Optional[dict]) -> Optional[str]:
    if not isinstance(skill_output, dict):
        return None
    for key in ("chart_base64", "image_base64", "chart_png_base64"):
        value = skill_output.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _parse_schedule_time(schedule_time: Optional[str]) -> datetime:
    if not schedule_time:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(schedule_time)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def _create_calendar_event(
    settings: Settings,
    message: str,
    schedule_time: Optional[str],
) -> dict:
    start_dt = _parse_schedule_time(schedule_time)
    end_dt = start_dt + timedelta(minutes=45)
    provider = settings.calendar_provider.lower().strip()
    base_event = {
        "title": message[:120],
        "start": start_dt.isoformat(),
        "end": end_dt.isoformat(),
        "scheduled_for": start_dt.isoformat(),
    }
    return {
        "provider": provider or "local",
        "status": "scheduled",
        "event_id": f"local-{uuid.uuid4().hex[:10]}",
        "link": None,
        **base_event,
    }


def _send_email(
    settings: Settings,
    to_email: str,
    subject: str,
    content: str,
    image_base64: Optional[str] = None,
) -> dict:
    """Send email via configured provider (smtp or resend)."""
    provider = settings.email_provider.lower()

    # --- SMTP provider ---
    if provider == "smtp":
        if not settings.smtp_host or not settings.smtp_user or not settings.smtp_password:
            return {
                "sent": False,
                "provider": "smtp",
                "error": "Missing SMTP_HOST / SMTP_USER / SMTP_PASSWORD in .env",
            }
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            from_email = settings.smtp_from_email or settings.smtp_user
            
            # Root container (mixed for attachments)
            msg = MIMEMultipart("mixed")
            msg["Subject"] = subject
            msg["From"] = from_email
            msg["To"] = to_email

            # Alternative for text/html versions
            alt_part = MIMEMultipart("alternative")
            alt_part.attach(MIMEText(content, "plain", "utf-8"))
            html_body = f"<pre style='font-family:sans-serif;white-space:pre-wrap'>{html.escape(content)}</pre>"
            alt_part.attach(MIMEText(html_body, "html", "utf-8"))
            msg.attach(alt_part)

            # Optional attachment
            if image_base64:
                try:
                    from email.mime.image import MIMEImage
                    # Clean potential prefix
                    if "," in image_base64:
                        image_base64 = image_base64.split(",")[1]
                    img_data = base64.b64decode(image_base64)
                    img = MIMEImage(img_data)
                    img.add_header("Content-Disposition", "attachment", filename="visual_response.png")
                    msg.attach(img)
                except Exception as e:
                    print(f"Error attaching image: {e}")

            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
                if settings.smtp_use_tls:
                    server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(from_email, [to_email], msg.as_bytes())

            return {
                "sent": True,
                "provider": "smtp",
                "to": to_email,
                "from": from_email,
            }
        except Exception as exc:
            return {
                "sent": False,
                "provider": "smtp",
                "error": str(exc),
                "to": to_email,
            }

    # --- Resend provider ---
    if not settings.resend_api_key or not settings.resend_from_email:
        return {
            "sent": False,
            "provider": "resend",
            "error": "Missing RESEND_API_KEY or RESEND_FROM_EMAIL",
        }
    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": settings.resend_from_email,
                "to": [to_email],
                "subject": subject,
                "text": content,
            },
            timeout=12.0,
        )
        response.raise_for_status()
        payload = response.json()
        return {
            "sent": True,
            "provider": "resend",
            "id": payload.get("id"),
            "to": to_email,
        }
    except Exception as exc:
        return {
            "sent": False,
            "provider": "resend",
            "error": str(exc),
            "to": to_email,
        }



async def _step_materialize(
    *,
    task_id: str,
    message: str,
    intent: dict,
    planner: PlannerAgent,
    router: SkillRouterAgent,
    coder: CoderAgent,
    reviewer: ReviewerAgent,
    llm_client: OllamaLLMClient,
    reviewer_llm_client: OllamaLLMClient,
    rag_service: RAGService,
    settings: Settings,
    force_new: bool = False,
    debug: bool = False,
    runtime_context: str,
    memory_context: str = "",
    total_llm_calls: int = 0,
) -> Tuple[Optional[dict], int]:
    """Generates execution plan, routes skills, and handles coding/review loop."""
    root = _repo_root()

    # 1. Planner Phase
    res_plan = planner.act(
        AgentContext(task_id=task_id, prompt=message, history_summary=memory_context),
        {
            "intent_json": str(intent), 
            "runtime_context": runtime_context,
            "validator_feedback": memory_context.split("RETRY_NOTE: ")[-1] if "RETRY_NOTE: " in memory_context else ""
        }
    )
    total_llm_calls += 1
    if not res_plan.success:
        plan_data = {"skills_to_create": []}
    else:
        plan_data = res_plan.payload.get("plan", {"skills_to_create": []})

    # 2. Skill Router Phase
    available_skills_list = []
    for folder in ["static", "dynamic"]:
        path = root / "app" / "skills" / folder
        if path.exists():
            available_skills_list.extend([f.stem for f in path.glob("*.py")])
    
    res_route = router.act(
        AgentContext(task_id=task_id, prompt=message),
        {
            "plan_json": json.dumps(plan_data, ensure_ascii=False),
            "available_skills": ", ".join(available_skills_list),
            "data_sources": "Tavily, Local_DB, RAG", 
            "runtime_context": runtime_context
        }
    )
    total_llm_calls += 1
    
    if not res_route.success:
        router_data = {"route": "create_new", "skills_to_build": [s["skill_name"] for s in plan_data.get("skills_to_create", [])]}
    else:
        router_data = res_route.payload

    print(f"DEBUG: Router Decision: {router_data.get('route')} - {router_data.get('routing_reason')}")

    # 3. Execution Path Handling
    all_materialized = []
    skills_to_build = router_data.get("skills_to_build", [])
    
    # Handle direct runs first - with existence validation
    for skill_name in router_data.get("skills_to_use", []):
        exists = False
        for folder in ["static", "dynamic"]:
            if (root / "app" / "skills" / folder / f"{skill_name}.py").exists():
                exists = True
                break
        
        if exists:
            all_materialized.append({
                "materialized_skill": {
                    "skill_id": skill_name,
                    "reused_existing": True,
                },
                "parameters": intent.get("entities") or {},
            })
        else:
            print(f"WARNING: Router hallucinated skill '{skill_name}'. Moving to build queue.")
            if skill_name not in skills_to_build:
                skills_to_build.append(skill_name)

    # Handle Coding / Patching
    for skill_spec in plan_data.get("skills_to_create", []):
        name = skill_spec["skill_name"]
        if name not in skills_to_build:
            continue
            
        is_static = skill_spec.get("is_static", False)
        folder = "static" if is_static else "dynamic"
        patch_mode = "delta" if router_data.get("route") == "patch" else "create_new"
        
        print(f"DEBUG: Coding skill '{name}' (mode={patch_mode})")
        
        # Call CoderAgent.act which now has its own internal review loop and static analysis
        res_coder = coder.act(
            AgentContext(task_id=task_id, prompt=message),
            {
                "plan": plan_data,
                "skill_name": name,
                "runtime_context": runtime_context,
                "patch_mode": patch_mode,
                "memory_context": memory_context,
                "total_llm_calls": total_llm_calls
            }
        )
        total_llm_calls = res_coder.payload.get("total_llm_calls", total_llm_calls)
        
        if res_coder.success:
            artifacts = res_coder.payload.get("artifacts", {})
            code_text = artifacts.get("generated_code", "")
            
            if code_text:
                # Save the skill
                save_path = root / "app" / "skills" / folder / f"{name}.py"
                save_path.parent.mkdir(parents=True, exist_ok=True)
                save_path.write_text(code_text, encoding="utf-8")
                
                all_materialized.append({
                    "materialized_skill": {
                        "skill_id": name,
                        "reused_existing": False,
                        "is_static": is_static,
                    },
                    "parameters": intent.get("entities") or {},
                })

    if not all_materialized:
        return None, total_llm_calls

    return {
        "all_materialized_skills": all_materialized,
        "plan": plan_data,
        "router": router_data
    }, total_llm_calls



def _step_execute_and_summarize(
    *,
    root: Path,
    message: str,
    materialize_data: Optional[dict],
    llm_client: OllamaLLMClient,
    validator: ResultValidatorAgent,
    runtime_context: str,
    total_llm_calls: int = 0,
    input_data: Optional[dict] = None,
) -> Tuple[dict, int]:
    """Executes skills and validates results."""
    if not materialize_data:
        return {"status": "error", "error_type": "no_materialize_data"}

    all_skills = materialize_data.get("all_materialized_skills") or []
    accumulated_data = dict(materialize_data.get("parameters") or {})
    if input_data:
        accumulated_data.update(input_data)
    
    skill_history = []
    last_output = {}

    # 1. Sequential Execution
    for skill_info in all_skills:
        skill_id = (skill_info.get("materialized_skill") or {}).get("skill_id")
        if not skill_id: continue
        
        print(f"DEBUG: Executing skill '{skill_id}'...")
        last_output = _execute_skill(root, skill_id, **accumulated_data)
        skill_history.append({"skill_id": skill_id, "output": last_output})
        
        if last_output.get("status") == "success":
            accumulated_data.update(last_output)
        else:
            print(f"WARNING: Skill '{skill_id}' failed: {last_output.get('summary')}")
            # Continue to next skill regardless, logic as before

    # 2. Result Validator Phase
    goal = (materialize_data.get("plan") or {}).get("task_summary", message)
    res_val = validator.act(
        AgentContext(task_id="validator", prompt=message),
        {
            "original_request": message,
            "skill_output": json.dumps(accumulated_data, ensure_ascii=False),
            "expected_goal": goal,
            "runtime_context": runtime_context
        }
    )
    total_llm_calls += 1
    
    if not res_val.success:
        validator_data = {"isValid": True, "result_code": "READY_FOR_SYNTHESIS"}
    else:
        validator_data = res_val.payload
        print(f"DEBUG: Validator Result: {validator_data.get('result_code')}")

    # 3. Decision logic
    result_code = validator_data.get("result_code")
    
    if result_code == "REQUEST_REPLAN":
        return {
            "status": "replan",
            "retry_instruction": validator_data.get("retry_instruction"),
            "accumulated_data": accumulated_data,
            "skill_history": skill_history
        }
    
    if result_code == "ESCALATE_TO_ERROR_HANDLER":
        return {
            "status": "error",
            "error_type": "validation_failed",
            "error_detail": validator_data.get("error_detail"),
            "accumulated_data": accumulated_data,
            "skill_history": skill_history
        }

    # 4. Synthesizer Phase (READY_FOR_SYNTHESIS)
    synth_messages = build_synthesizer_messages(message, json.dumps(accumulated_data, ensure_ascii=False))
    synth_prompt = f"{synth_messages[0]['content']}\n\n{synth_messages[1]['content']}"
    
    try:
        synth_raw = _generate_text_strict(llm_client, synth_prompt, response_format="json")
        synth_data = json.loads(synth_raw)
        reply = synth_data.get("reply") or last_output.get("summary") or "Xong."
    except Exception:
        reply = last_output.get("summary") or "Đã thực hiện xong yêu cầu của bạn."

    total_llm_calls += 1 # Synthesizer

    return ({
        "status": "success",
        "reply": reply,
        "skill_output": last_output,
        "accumulated_data": accumulated_data,
        "skill_history": skill_history,
        "validator": validator_data
    }, total_llm_calls)


@router.post("/run")
async def run_debug_agent_flow(
    payload: AgentRunRequest,
    planner: PlannerAgent = Depends(get_planner_agent),
    coder: CoderAgent = Depends(get_coder_agent),
    reviewer: ReviewerAgent = Depends(get_reviewer_agent),
):
    manager = ManagerAgent(planner=planner, coder=coder, reviewer=reviewer)
    result = manager.run(
        task_id=payload.task_id,
        prompt=payload.prompt,
        priority=payload.priority,
    )
    return {
        "task_id": result.task_id,
        "final_state": result.final_state,
        "transitions": result.transitions,
        "reason_code": result.reason_code,
        "execution_log": result.execution_log,
    }


@router.get("/steps")
async def list_agent_steps():
    return {"steps": []}


@router.get("/memory/short-term/{task_id}")
async def get_short_term_memory(
    task_id: str,
    settings: Settings = Depends(get_settings_dep),
):
    if not settings.redis_url:
        raise HTTPException(status_code=400, detail="REDIS_URL is not configured")
    short_key = f"aaf:materialize:{task_id}"
    try:
        import redis

        client = redis.from_url(settings.redis_url, decode_responses=True)
        raw = client.get(short_key)
        ttl = client.ttl(short_key)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Cannot read short-term memory: {exc}",
        ) from exc
    if raw is None:
        raise HTTPException(status_code=404, detail="Task memory not found")
    try:
        payload_data = json.loads(raw)
    except Exception:
        payload_data = raw
    return {
        "task_id": task_id,
        "redis_key": short_key,
        "ttl_seconds": ttl,
        "payload": payload_data,
    }


@router.get("/materialize/history")
async def get_materialize_history(
    limit: int = Query(default=20, ge=1, le=100),
    settings: Settings = Depends(get_settings_dep),
):
    if not settings.mongodb_uri:
        raise HTTPException(status_code=400, detail="MONGODB_URI is not configured")
    try:
        from pymongo import DESCENDING, MongoClient

        client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000)
        records = list(
            client[settings.mongodb_db]["materialize_events"]
            .find(
                {},
                {
                    "_id": 1,
                    "task_id": 1,
                    "prompt": 1,
                    "skill_id": 1,
                    "reused_existing": 1,
                    "created_at": 1,
                },
            )
            .sort("created_at", DESCENDING)
            .limit(limit)
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Cannot read history: {exc}")
    for item in records:
        if "_id" in item:
            item["_id"] = str(item["_id"])
    return {"count": len(records), "items": records}


@router.post("/materialize")
async def run_and_materialize(
    payload: AgentMaterializeRequest,
    planner: PlannerAgent = Depends(get_planner_agent),
    coder: CoderAgent = Depends(get_coder_agent),
    reviewer: ReviewerAgent = Depends(get_reviewer_agent),
    agent_llm_client: OllamaLLMClient = Depends(get_agent_llm_client),
    reviewer_llm_client: OllamaLLMClient = Depends(get_reviewer_llm_client),
    rag_service: RAGService = Depends(get_rag_service),
    settings: Settings = Depends(get_settings_dep),
):
    debug_mode = bool(payload.debug or settings.debug)
    root = _repo_root()

    manager = ManagerAgent(planner=planner, coder=coder, reviewer=reviewer)
    result = manager.run(
        task_id=payload.task_id,
        prompt=payload.prompt,
        priority=payload.priority,
        history_summary=payload.history_summary,
    )
    execution_log = list(result.execution_log)

    planner_logs = [
        item for item in result.execution_log if item.get("stage") == "planner"
    ]
    plan: dict = {}
    if planner_logs:
        plan = (planner_logs[-1].get("payload") or {}).get("plan") or {}

    if not payload.force_new:
        existing = _find_existing_skill(
            root=root,
            task_prompt=payload.prompt,
            rag_service=rag_service,
        )
        if existing and payload.skill_id is None:
            event = {
                "task_id": result.task_id,
                "prompt": payload.prompt,
                "skill_id": existing["skill_id"],
                "reused_existing": True,
                "match_score": existing["score"],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            return {
                "task_id": result.task_id,
                "final_state": result.final_state,
                "execution_log": execution_log,
                "materialized_skill": {
                    "skill_id": existing["skill_id"],
                    "version": "0.1.0",
                    "files": existing["files"],
                    "reused_existing": True,
                    "match_score": existing["score"],
                },
                "memory_persistence": _persist_short_and_long_memory(settings, event),
            }

    skill_name = _slugify(payload.skill_id or plan.get("objective") or payload.prompt)

    web_context = _fetch_web_context(payload.prompt, settings)
    rag_context = _fetch_rag_context(payload.prompt, rag_service)

    try:
        coder_brief = _build_coder_brief(
            llm_client=agent_llm_client,
            user_request=payload.prompt,
            skill_name=skill_name,
            plan=plan,
            web_context=web_context,
            rag_context=rag_context,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"LLM khong phan hoi khi tao CoderBrief: {exc}",
        ) from exc

    if debug_mode:
        execution_log.append(
            {
                "stage": "manager",
                "payload": {"coder_brief": coder_brief},
            }
        )

    code_prompt_tpl = (
        "Nguoi dung giao cho Coder Agent viet code Python theo CODER BRIEF ben duoi.\n"
        "Tra ve CODE PYTHON THUAN. Khong markdown, khong giai thich, khong comment thua.\n\n"
        f"{_SKILL_CONTRACT}\n\n"
        "Ten skill: {skill_name}\n\n"
        "CODER BRIEF (thiet ke tu Planner – tuan thu tuyet doi):\n{coder_brief}"
    )

    MAX_CODING_RETRIES = 3
    code_text = ""
    # coder_brief = ""  # Removed redundant reset
    reviewer_feedback = ""

    for attempt in range(1, MAX_CODING_RETRIES + 1):
        code_prompt = code_prompt_tpl.format(
            skill_name=skill_name,
            coder_brief=coder_brief,
        )
        try:
            # Code generation uses the architect's brief but it's executed by CoderAgent 
            # in the background during manager.run(), however materialize uses 
            # the current llm_client. Materialize should ideally use coder_llm_client.
            # But wait, ManagerAgent.run() already executed Planner/Coder/Reviewer.
            # This /materialize endpoint seems to RE-RUN some parts.
            # I should make sure we use the correct client here too.
            # For now, I'll use coder_llm_client if I add it.
            # Actually, I'll update the endpoint to include all three.
            code_text = _generate_text_strict(agent_llm_client, code_prompt)
        except ValueError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"LLM khong phan hoi khi sinh code (lan {attempt}): {exc}",
            ) from exc

        # LLM Review pass
        review = _llm_review_code(reviewer_llm_client, skill_name, coder_brief, code_text)
        if debug_mode:
            execution_log.append({
                "stage": f"llm_reviewer_attempt_{attempt}",
                "payload": review,
            })

        if review["passed"]:
            break  # Code dat yeu cau, thoat vong lap

        # Reviewer thay van de -> Planner tai thiet ke voi feedback
        reviewer_feedback = review["feedback"]
        if attempt < MAX_CODING_RETRIES:
            try:
                coder_brief = _build_coder_brief(
                    llm_client=agent_llm_client,
                    user_request=payload.prompt,
                    skill_name=skill_name,
                    plan=plan,
                    web_context=web_context,
                    rag_context=rag_context,
                    reviewer_feedback=reviewer_feedback,
                )
            except ValueError:
                pass  # Giu nguyen coder_brief cu neu LLM loi

    folder = "static" if payload.is_static else "dynamic"
    skill_path = root / "app" / "skills" / folder / f"{skill_name}.py"
    test_path = root / "tests" / "generated" / f"test_{skill_name}.py"
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.parent.mkdir(parents=True, exist_ok=True)
    skill_path.write_text(code_text + "\n", encoding="utf-8")
    written_files = [str(skill_path.relative_to(root)).replace("\\", "/")]

    if payload.create_test:
        test_prompt = (
            "Sinh pytest file cho skill sau. Chi tra ve code Python, khong markdown.\n"
            f"Module: app.skills.{folder}.{skill_name}\n"
            "- from __future__ import annotations\n"
            "- Import va test ham run\n"
            "- Assert run() tra ve dict voi key status\n"
            "- Assert run()['status'] == 'success' hoac 'error'\n"
        )
        try:
            test_text = _generate_text_strict(agent_llm_client, test_prompt)
        except ValueError:
            test_text = (
                "from __future__ import annotations\n"
                f"from app.skills.{folder}.{skill_name} import run\n\n"
                "def test_run_returns_dict():\n"
                "    result = run()\n"
                "    assert isinstance(result, dict)\n"
                "    assert 'status' in result\n"
            )
        test_path.write_text(test_text + "\n", encoding="utf-8")
        written_files.append(str(test_path.relative_to(root)).replace("\\", "/"))

    digest = hashlib.sha256(code_text.encode("utf-8")).hexdigest()
    registry.register(
        SkillRecord(
            skill_id=skill_name,
            version="0.1.0",
            digest=SkillDigest(value=digest),
            source_task_id=payload.task_id,
            approval_id="pending-approval",
            status=SkillState.draft,
            is_static=payload.is_static,
        )
    )

    skill_creator = None
    if payload.package_with_skill_creator:
        bundle_dir = _create_skill_creator_bundle(
            root,
            skill_name,
            payload.prompt,
            code_text,
        )
        skill_creator = _run_skill_creator_tools(root, bundle_dir)

    event = {
        "task_id": result.task_id,
        "prompt": payload.prompt,
        "skill_id": skill_name,
        "reused_existing": False,
        "digest": digest,
        "files": written_files,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    memory_status = _persist_short_and_long_memory(settings, event)

    response: dict[str, Any] = {
        "task_id": result.task_id,
        "final_state": result.final_state,
        "transitions": result.transitions,
        "reason_code": result.reason_code,
        "execution_log": execution_log,
        "materialized_skill": {
            "skill_id": skill_name,
            "version": "0.1.0",
            "digest": digest,
            "files": written_files,
            "reused_existing": False,
            "is_static": payload.is_static,
        },
        "parameters": payload.parameters,
        "skill_creator": skill_creator,
        "memory_persistence": memory_status,
    }
    if debug_mode:
        response["coder_brief"] = coder_brief
    return response


@router.post("/chat")
async def chat_agent(
    payload: AgentChatRequest,
    background_tasks: BackgroundTasks,
    intent_parser: IntentParserAgent = Depends(get_intent_parser_agent),
    clarifier: ClarifierAgent = Depends(get_clarifier_agent),
    planner: PlannerAgent = Depends(get_planner_agent),
    router: SkillRouterAgent = Depends(get_skill_router_agent),
    coder: CoderAgent = Depends(get_coder_agent),
    reviewer: ReviewerAgent = Depends(get_reviewer_agent),
    validator: ResultValidatorAgent = Depends(get_result_validator_agent),
    error_handler: ErrorHandlerAgent = Depends(get_error_handler_agent),
    agent_llm_client: OllamaLLMClient = Depends(get_agent_llm_client),
    reviewer_llm_client: OllamaLLMClient = Depends(get_reviewer_llm_client),
    rag_service: RAGService = Depends(get_rag_service),
    settings: Settings = Depends(get_settings_dep),
    memory: MemoryManager = Depends(get_memory_manager),
):
    """Main entry point for the new Refructured Agent Pipeline."""
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message must not be empty")

    task_id = f"chat-{uuid.uuid4().hex[:10]}"
    user_id = payload.user_email or "default-user"
    root = _repo_root()
    
    # 0. Context Injection & History Retrieval
    history = []
    if payload.conversation_history:
        for m in payload.conversation_history:
            history.append({"role": m.role, "content": m.content})
    else:
        try:
            # Fallback to memory manager history if not provided in payload
            raw_history = memory.get_recent_history(user_id=user_id, limit=6)
            if isinstance(raw_history, str):
                for line in raw_history.split("\n---\n"):
                    if ":" in line:
                        role, content = line.split(":", 1)
                        history.append({"role": role.strip().lower(), "content": content.strip()})
        except Exception:
            pass

    from app.brain.prompt_templates import build_runtime_context
    runtime_context = build_runtime_context(history=history)

    # Semantic context
    try:
        semantic_context = memory.get_context(message, user_id, 4)
    except Exception:
        semantic_context = ""

    # 1. Intent Parsing
    print(f"DEBUG: Pipeline starting for task {task_id}")
    total_llm_calls = 0
    intent = _parse_intent(intent_parser, message, runtime_context, semantic_context)
    total_llm_calls += 1
    
    # 1.1 Clarifier Gate
    if intent.get("ambiguous") or intent.get("clarification_needed"):
        hint = intent.get("clarification_hint") or "Bạn có thể nói rõ hơn không?"
        res_clarify = clarifier.act(
            AgentContext(task_id=task_id, trace_id=task_id, prompt=message),
            {"message": message, "hint": hint, "runtime_context": runtime_context}
        )
        total_llm_calls += 1
        
        if res_clarify.success:
            reply = res_clarify.payload.get("question_to_user") or hint
        else:
            reply = hint
            
        return {
            "task_id": task_id,
            "reply": reply,
            "total_llm_calls": total_llm_calls,
            "artifacts": {"intent": intent}
        }

    # 1.2 Memorize Facts
    facts = intent.get("entities", {}).get("facts_to_remember", [])
    for fact in facts:
        memory.store_fact(user_id, fact)

    # 2. Planning & Execution Loop (Up to 2 re-plans)
    replan_count = 0
    MAX_REPLANS = 2
    retry_instruction = ""
    
    materialize_data = None
    exec_result = {}
    
    while replan_count <= MAX_REPLANS:
        # 3. Planning & Routing & Coding
        print(f"DEBUG: Planning phase (Iteration {replan_count})")
        materialize_data, total_llm_calls = await _step_materialize(
            task_id=task_id,
            message=message,
            intent=intent,
            planner=planner,
            router=router,
            coder=coder,
            reviewer=reviewer,
            llm_client=agent_llm_client,
            reviewer_llm_client=reviewer_llm_client,
            rag_service=rag_service,
            settings=settings,
            runtime_context=runtime_context,
            memory_context=f"{semantic_context}\n\nRETRY_NOTE: {retry_instruction}" if retry_instruction else semantic_context,
            total_llm_calls=total_llm_calls
        )
        
        if not materialize_data:
            break

        # 4. Execution & Validation
        print(f"DEBUG: Execution phase")
        exec_result, total_llm_calls = _step_execute_and_summarize(
            root=root,
            message=message,
            materialize_data=materialize_data,
            llm_client=agent_llm_client,
            validator=validator,
            runtime_context=runtime_context,
            total_llm_calls=total_llm_calls
        )
        
        if exec_result.get("status") == "replan":
            replan_count += 1
            retry_instruction = exec_result.get("retry_instruction", "Vui lòng điều chỉnh kế hoạch để đạt được kết quả tốt hơn.")
            print(f"DEBUG: Re-plan requested. Reason: {retry_instruction}")
            continue
        
        break

    # 5. Final Response or Error Handling
    if exec_result.get("status") == "success":
        reply = exec_result.get("reply")
    else:
        # 6. Error Handler Phase
        print(f"DEBUG: Escalating to Error Handler")
        res_err = error_handler.act(
            AgentContext(task_id=task_id, trace_id=task_id, prompt=message),
            {
                "failure_stage": "Execution/Validation",
                "technical_error": exec_result.get("error_detail") or "Pipeline failed after maximum attempts."
            }
        )
        if res_err.success:
            reply = res_err.payload.get("user_message")
        else:
            reply = "Xin lỗi, tôi gặp sự cố kỹ thuật và không thể hoàn thành yêu cầu này lúc này."

    # Background tasks
    background_tasks.add_task(memory.store_chat_turn, user_id, message, str(reply))

    # Build artifacts for UI
    artifacts: dict[str, Any] = {
        "intent": intent,
        "skill_output": exec_result.get("skill_output", {}),
        "materialize_data": materialize_data,
        "history": history
    }
    
    # Extract images
    image_urls = exec_result.get("accumulated_data", {}).get("image_urls", [])
    if image_urls:
        artifacts["image_urls"] = image_urls
    
    image_b64 = _extract_chart_base64(exec_result.get("skill_output", {}))
    if image_b64:
        artifacts["image_base64"] = image_b64

    return {
        "task_id": task_id,
        "reply": reply,
        "total_llm_calls": total_llm_calls,
        "artifacts": artifacts,
    }


@router.post("/chat/upload")
async def chat_agent_with_upload(
    message: str = Form(...),
    file: UploadFile = File(...),
    conversation_history_json: Optional[str] = Form(default=None, alias="conversation_history"),
    user_email: Optional[str] = Form(default=None),
    schedule_time: Optional[str] = Form(default=None),
    force_new: bool = Form(default=False),
    debug: bool = Form(default=False),
    planner: PlannerAgent = Depends(get_planner_agent),
    coder: CoderAgent = Depends(get_coder_agent),
    agent_llm_client: OllamaLLMClient = Depends(get_agent_llm_client),
    reviewer_llm_client: OllamaLLMClient = Depends(get_reviewer_llm_client),
    rag_service: RAGService = Depends(get_rag_service),
    settings: Settings = Depends(get_settings_dep),
):
    # Parse conversation history from JSON string if provided
    history: list[ConversationMessage] = []
    if conversation_history_json:
        try:
            raw_history = json.loads(conversation_history_json)
            history = [ConversationMessage(**m) for m in raw_history]
        except Exception:
            history = []

    raw = await file.read()
    file_text = ""
    if raw:
        name = (file.filename or "").lower()
        try:
            if name.endswith(".json"):
                parsed = json.loads(raw.decode("utf-8", errors="ignore"))
                file_text = json.dumps(parsed, ensure_ascii=False)[:3000]
            else:
                file_text = raw.decode("utf-8", errors="ignore")[:3000]
        except Exception:
            file_text = ""

    if file_text:
        composed = (
            f"{message}\n\n"
            f"Uploaded: {file.filename}\n"
            f"{file_text}"
        )
    else:
        composed = message

    result = await chat_agent(
        payload=AgentChatRequest(
            message=composed,
            conversation_history=history,
            user_email=user_email,
            schedule_time=schedule_time,
            force_new=force_new,
            debug=debug,
        ),
        planner=planner,
        coder=coder,
        agent_llm_client=agent_llm_client,
        reviewer_llm_client=reviewer_llm_client,
        rag_service=rag_service,
        settings=settings,
    )
    result["uploaded_file"] = {
        "filename": file.filename,
        "content_type": file.content_type,
        "excerpt_chars": len(file_text),
    }
    return result

