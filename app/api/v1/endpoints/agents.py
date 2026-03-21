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
from typing import Any, Optional

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query
from fastapi import UploadFile
from pydantic import BaseModel, Field

from app.api.dependencies import (
    get_coder_agent,
    get_llm_client,
    get_planner_agent,
    get_rag_service,
    get_settings_dep,
)
from app.agents.coder import CoderAgent
from app.agents.manager import ManagerAgent
from app.brain.prompt_templates import (
    build_coder_messages,
    build_manager_orchestrator_messages,
    build_test_generation_messages,
)
from app.brain.planner import PlannerAgent
from app.brain.rag import RAGService
from app.core.config import Settings
from app.infrastructure.external_apis.ollama_client import OllamaLLMClient
from app.schemas.skills import SkillDigest, SkillState
from app.skills.registry import SkillRecord, registry

router = APIRouter()


class AgentRunRequest(BaseModel):
    task_id: str = Field(default="debug-task")
    prompt: str
    priority: str = Field(default="standard")


class AgentMaterializeRequest(BaseModel):
    task_id: str = Field(default="materialize-task")
    prompt: str
    priority: str = Field(default="standard")
    skill_id: Optional[str] = Field(default=None)
    create_test: bool = Field(default=True)
    package_with_skill_creator: bool = Field(default=True)
    force_new: bool = Field(default=False)
    debug: bool = Field(default=False)


class AgentChatRequest(BaseModel):
    message: str
    user_email: Optional[str] = Field(default=None)
    schedule_time: Optional[str] = Field(default=None)
    force_new: bool = Field(default=False)
    debug: bool = Field(default=False)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _generate_text_strict(
    llm_client: OllamaLLMClient,
    prompt: str,
) -> str:
    text: str = llm_client.generate(prompt=prompt)
    text = _strip_code_fences(text.strip())
    if not text:
        raise ValueError("LLM tra ve response rong. Kiem tra model/connection.")
    return text


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_\-]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    return cleaned.strip()


_INTENT_SCHEMA = """\
Tra ve JSON duy nhat, khong markdown, khong giai thich:
{
  \"wants_skill\": true/false,
  \"wants_report\": true/false,
  \"wants_image\": true/false,
  \"wants_schedule\": true/false,
  \"wants_email\": true/false,
  \"skill_hint\": \"string\"
}"""


def _detect_intent(llm_client: OllamaLLMClient, message: str) -> dict:
    prompt = (
        "Phan tich yeu cau nguoi dung sau va tra ve JSON theo schema:\n"
        f"Yeu cau: \"{message}\"\n\n"
        f"Schema:\n{_INTENT_SCHEMA}\n\n"
        "Luu y: wants_skill=true khi user can du lieu that (gia, thong ke, "
        "tra cuu, tinh toan, phan tich) - khong phai cau hoi chung chung."
    )
    try:
        raw = _generate_text_strict(llm_client, prompt)
        intent = json.loads(raw)
        defaults = {
            "wants_skill": False,
            "wants_report": False,
            "wants_image": False,
            "wants_schedule": False,
            "wants_email": False,
            "skill_hint": "",
        }
        defaults.update(intent)
        return defaults
    except Exception as exc:
        return {
            "wants_skill": False,
            "wants_report": False,
            "wants_image": False,
            "wants_schedule": False,
            "wants_email": False,
            "skill_hint": "",
            "_intent_error": str(exc),
        }


_SKILL_CONTRACT = """\
## Chuan skill trong du an AAF-AIOS

### Vi tri file
- Skill module: app/skills/dynamic/{skill_name}.py
- Test file: tests/generated/test_{skill_name}.py

### Interface bat buoc
from __future__ import annotations
from typing import Any, Dict

def run(input_data: Dict[str, Any] | None = None) -> Dict[str, Any]:
    \"\"\"Entry point duy nhat. KHONG dinh nghia class.\"\"\"
    ...

### Output contract bat buoc
Moi skill PHAI tra ve dict chua:
- status: success | error
- collected_at: ISO datetime string
- source_urls: list[str] - nguon du lieu thuc te
- summary: str - tom tat ket qua bang tieng Viet
- Cac key nghiep vu cu the cua skill

### Quy tac bat buoc
1. KHONG bia so lieu. Neu khong lay duoc du lieu that -> status=error voi error_reason.
2. Dung httpx de goi API.
3. Wrap logic trong try/except, tra ve error dict thay vi raise.
4. KHONG dung requests, KHONG import thu vien ngoai project.
5. Neu can scraping -> dung httpx.get(url).text va parse regex/str.
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
) -> str:
    plan_text = _plan_to_text(plan)
    messages = build_manager_orchestrator_messages(
        user_request=user_request,
        skill_name=skill_name,
        plan_json=plan_text,
        web_context=web_context[:1500],
        rag_context=rag_context[:800],
        runtime_context="",
        planning_topology="graph_of_thoughts",
    )

    prompt = (
        f"{messages[1]['content']}\n\n"
        "## Skill Runtime Contract (bat buoc)\n"
        f"{_SKILL_CONTRACT}"
    )
    text: str = llm_client.generate(
        prompt=prompt,
        system_prompt=messages[0]["content"],
    )
    text = _strip_code_fences(text.strip())
    if not text:
        raise ValueError("LLM tra ve response rong. Kiem tra model/connection.")
    return text


def _execute_skill(
    root: Path,
    skill_name: str,
    input_data: Optional[dict] = None,
) -> dict:
    candidates = [
        root / "app" / "skills" / "dynamic" / f"{skill_name}.py",
        root / "app" / "skills" / "static" / f"{skill_name}.py",
    ]
    skill_path = next((path for path in candidates if path.exists()), None)
    if skill_path is None:
        return {
            "status": "error",
            "error_reason": (
                "Skill file not found in dynamic/static: "
                f"{skill_name}.py"
            ),
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }

    module_name = f"aaf_skill_{uuid.uuid4().hex[:8]}"
    try:
        spec = importlib.util.spec_from_file_location(module_name, skill_path)
        if spec is None or spec.loader is None:
            raise ImportError("Cannot load skill spec")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        run_fn = getattr(module, "run", None)
        if not callable(run_fn):
            raise AttributeError("Skill khong co ham run()")

        payload = input_data if isinstance(input_data, dict) else {}
        try:
            output = run_fn(input_data=payload)
        except TypeError:
            # Backward compatibility for legacy skills with run() no args.
            output = run_fn()
        if not isinstance(output, dict):
            return {
                "status": "error",
                "error_reason": (
                    f"run() tra ve {type(output).__name__}, expected dict"
                ),
                "raw_output": str(output)[:500],
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
    dynamic_root = root / "app" / "skills" / "dynamic"
    if dynamic_root.exists():
        for skill_file in dynamic_root.glob("*.py"):
            try:
                metadata_text = skill_file.read_text(encoding="utf-8")[:2000]
                skill_id = skill_file.stem
                rag_service.ingest(
                    record_id=f"existing-skill-{skill_id}",
                    text=f"skill_id={skill_id}\n{metadata_text}",
                    metadata={"type": "existing_skill", "skill_id": skill_id},
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
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    lines = escaped.splitlines()[:5] or [escaped]
    svg_lines = []
    y = 58
    for line in lines:
        svg_lines.append(
            f'<text x="24" y="{y}" fill="#112" '
            'font-size="20" font-family="Arial">'
            f"{line[:70]}</text>"
        )
        y += 34
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1024" '
        'height="512">'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0%" stop-color="#ffe8c8"/>'
        '<stop offset="100%" stop-color="#d6f3ee"/>'
        '</linearGradient></defs>'
        '<rect width="1024" height="512" fill="url(#g)" rx="26"/>'
        f"{''.join(svg_lines)}"
        "</svg>"
    )
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
) -> dict:
    if settings.email_provider.lower() != "resend":
        return {
            "sent": False,
            "provider": settings.email_provider,
            "error": "Only resend provider is implemented",
        }
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
    coder: CoderAgent,
    llm_client: OllamaLLMClient,
    rag_service: RAGService,
    settings: Settings,
    force_new: bool,
    debug: bool,
) -> Optional[dict]:
    if not intent.get("wants_skill") and not intent.get("wants_report"):
        return None

    return await run_and_materialize(
        payload=AgentMaterializeRequest(
            task_id=task_id,
            prompt=message,
            priority="standard",
            skill_id=intent.get("skill_hint") or None,
            create_test=True,
            package_with_skill_creator=True,
            force_new=force_new,
            debug=debug,
        ),
        planner=planner,
        coder=coder,
        llm_client=llm_client,
        rag_service=rag_service,
        settings=settings,
    )


def _step_execute_and_summarize(
    *,
    root: Path,
    message: str,
    materialize_data: Optional[dict],
    llm_client: OllamaLLMClient,
) -> dict:
    if not materialize_data:
        return {"skill_output": None, "reply": None}

    skill_id = (materialize_data.get("materialized_skill") or {}).get("skill_id")
    if not skill_id:
        return {"skill_output": None, "reply": None}

    skill_output = _execute_skill(root, skill_id)

    if skill_output.get("status") == "error":
        reply = (
            f"Skill {skill_id} gap loi khi chay: "
            f"{skill_output.get('error_reason', 'Unknown error')}. "
            "Vui long thu lai hoac lien he admin."
        )
    else:
        summary_prompt = (
            f"Nguoi dung hoi: \"{message}\"\n\n"
            "Ket qua tu skill:\n"
            f"{json.dumps(skill_output, ensure_ascii=False, indent=2)[:2000]}\n\n"
            "Hay tom tat ket qua thanh 2-4 cau tieng Viet tu nhien, "
            "ro rang, khong lo ten skill hay key ky thuat. "
            "Chi tra ve phan tom tat, khong giai thich them."
        )
        try:
            reply = _generate_text_strict(llm_client, summary_prompt)
        except Exception as exc:
            reply = skill_output.get("summary") or f"Da xu ly xong. (LLM error: {exc})"

    return {"skill_output": skill_output, "reply": reply}


@router.post("/run")
async def run_debug_agent_flow(
    payload: AgentRunRequest,
    planner: PlannerAgent = Depends(get_planner_agent),
    coder: CoderAgent = Depends(get_coder_agent),
):
    manager = ManagerAgent(planner=planner, coder=coder)
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
    llm_client: OllamaLLMClient = Depends(get_llm_client),
    rag_service: RAGService = Depends(get_rag_service),
    settings: Settings = Depends(get_settings_dep),
):
    debug_mode = bool(payload.debug or settings.debug)
    root = _repo_root()

    manager = ManagerAgent(planner=planner, coder=coder)
    result = manager.run(
        task_id=payload.task_id,
        prompt=payload.prompt,
        priority=payload.priority,
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

    skill_name = payload.skill_id or _slugify(plan.get("objective") or payload.prompt)

    web_context = _fetch_web_context(payload.prompt, settings)
    rag_context = _fetch_rag_context(payload.prompt, rag_service)

    try:
        coder_brief = _build_coder_brief(
            llm_client=llm_client,
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

    coder_plan = {
        "task_summary": str(plan.get("task_summary") or plan.get("objective") or payload.prompt),
        "skills_to_create": [
            {
                "skill_name": skill_name,
                "skill_purpose": str(plan.get("task_summary") or payload.prompt),
                "coder_notes": coder_brief,
            }
        ],
    }
    coder_messages = build_coder_messages(
        plan_json=json.dumps(coder_plan, ensure_ascii=False),
        skill_name=skill_name,
        runtime_context="",
        memory_context=(
            f"Web context:\n{web_context[:1000]}\n\n"
            f"RAG context:\n{rag_context[:800]}"
        ),
        patch_mode="create_new",
    )
    code_prompt = (
        f"{coder_messages[1]['content']}\n\n"
        f"## Skill Runtime Contract (bat buoc)\n{_SKILL_CONTRACT}"
    )
    try:
        code_text = str(
            llm_client.generate(
                prompt=code_prompt,
                system_prompt=coder_messages[0]["content"],
            )
        ).strip()
        code_text = _strip_code_fences(code_text)
        if not code_text:
            raise ValueError("LLM tra ve response rong. Kiem tra model/connection.")
    except ValueError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"LLM khong phan hoi khi sinh code: {exc}",
        ) from exc

    skill_path = root / "app" / "skills" / "dynamic" / f"{skill_name}.py"
    test_path = root / "tests" / "generated" / f"test_{skill_name}.py"
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.parent.mkdir(parents=True, exist_ok=True)
    skill_path.write_text(code_text + "\n", encoding="utf-8")
    written_files = [str(skill_path.relative_to(root)).replace("\\", "/")]

    if payload.create_test:
        test_prompt = build_test_generation_messages(
            module_path=f"app.skills.dynamic.{skill_name}"
        )[0]["content"]
        try:
            test_text = _generate_text_strict(llm_client, test_prompt)
        except ValueError:
            test_text = (
                "from __future__ import annotations\n"
                f"from app.skills.dynamic.{skill_name} import run\n\n"
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
        },
        "skill_creator": skill_creator,
        "memory_persistence": memory_status,
    }
    if debug_mode:
        response["coder_brief"] = coder_brief
    return response


@router.post("/chat")
async def chat_agent(
    payload: AgentChatRequest,
    planner: PlannerAgent = Depends(get_planner_agent),
    coder: CoderAgent = Depends(get_coder_agent),
    llm_client: OllamaLLMClient = Depends(get_llm_client),
    rag_service: RAGService = Depends(get_rag_service),
    settings: Settings = Depends(get_settings_dep),
):
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message must not be empty")

    task_id = f"chat-{uuid.uuid4().hex[:10]}"
    root = _repo_root()

    intent = _detect_intent(llm_client, message)

    materialize_data = await _step_materialize(
        task_id=task_id,
        message=message,
        intent=intent,
        planner=planner,
        coder=coder,
        llm_client=llm_client,
        rag_service=rag_service,
        settings=settings,
        force_new=payload.force_new,
        debug=payload.debug,
    )

    exec_result = _step_execute_and_summarize(
        root=root,
        message=message,
        materialize_data=materialize_data,
        llm_client=llm_client,
    )
    skill_output: Optional[dict] = exec_result.get("skill_output")
    reply: Optional[str] = exec_result.get("reply")

    if not reply:
        rag_ctx = _fetch_rag_context(message, rag_service)
        direct_prompt = (
            f"Nguoi dung hoi: \"{message}\"\n\n"
            f"Context tu knowledge base:\n{rag_ctx[:800]}\n\n"
            "Tra loi ngan gon, tu nhien bang tieng Viet."
        )
        try:
            reply = _generate_text_strict(llm_client, direct_prompt)
        except ValueError as exc:
            reply = f"Xin loi, he thong dang gap su co: {exc}"

    report_files = None
    report_markdown = None
    if intent.get("wants_report") and skill_output:
        report_markdown = (
            "# Bao Cao\n\n"
            f"- Thoi gian: {datetime.now(timezone.utc).isoformat()}\n"
            f"- Yeu cau: {message}\n\n"
            f"## Ket Qua\n\n{reply}\n\n"
            "## Du Lieu Chi Tiet\n\n"
            "```json\n"
            f"{json.dumps(skill_output, ensure_ascii=False, indent=2)}\n"
            "```\n"
        )
        report_files = _save_report_files(task_id, report_markdown)

    image_base64 = None
    if intent.get("wants_image"):
        image_base64 = _extract_chart_base64(skill_output)
        if not image_base64:
            image_base64 = _render_text_image_base64(reply or message)

    schedule_info = None
    if intent.get("wants_schedule"):
        schedule_info = _create_calendar_event(
            settings=settings,
            message=message,
            schedule_time=payload.schedule_time,
        )

    email_result = None
    if intent.get("wants_email") and payload.user_email:
        content = report_markdown or reply or message
        email_result = _send_email(
            settings=settings,
            to_email=payload.user_email,
            subject="AAF-AIOS Agent Result",
            content=content,
        )

    response: dict[str, Any] = {
        "task_id": task_id,
        "reply": reply,
        "artifacts": {
            "skill_output": skill_output,
            "report_markdown": report_markdown,
            "report_files": report_files,
            "image_base64": image_base64,
            "schedule": schedule_info,
            "email": email_result,
        },
    }
    if payload.debug:
        response["_debug"] = {
            "intent": intent,
            "materialize": materialize_data,
        }
    return response


@router.post("/chat/upload")
async def chat_agent_with_upload(
    message: str = Form(...),
    file: UploadFile = File(...),
    user_email: Optional[str] = Form(default=None),
    schedule_time: Optional[str] = Form(default=None),
    force_new: bool = Form(default=False),
    debug: bool = Form(default=False),
    planner: PlannerAgent = Depends(get_planner_agent),
    coder: CoderAgent = Depends(get_coder_agent),
    llm_client: OllamaLLMClient = Depends(get_llm_client),
    rag_service: RAGService = Depends(get_rag_service),
    settings: Settings = Depends(get_settings_dep),
):
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
            user_email=user_email,
            schedule_time=schedule_time,
            force_new=force_new,
            debug=debug,
        ),
        planner=planner,
        coder=coder,
        llm_client=llm_client,
        rag_service=rag_service,
        settings=settings,
    )
    result["uploaded_file"] = {
        "filename": file.filename,
        "content_type": file.content_type,
        "excerpt_chars": len(file_text),
    }
    return result
