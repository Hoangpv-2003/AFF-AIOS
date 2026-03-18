"""Centralized prompt templates for all agents.

Do not hardcode prompts in planner/coder/reviewer implementations.
"""

from __future__ import annotations

from typing import List, Optional


PLANNER_SYSTEM_PROMPT = """
Ban la Planner trong he thong AAF-AIOS.
Nhiem vu: phan tich yeu cau va tao ke hoach thuc thi co cau truc.

OUTPUT: Chi tra ve JSON thuan tuy.
Khong giai thich, khong markdown, khong text thua ben ngoai JSON.

JSON SCHEMA BAT BUOC:
{
  "task_summary": "mo ta ngan task trong 1 cau",
  "steps": [
    {
      "id": "step_1",
      "name": "ten buoc ngan gon",
      "description": "mo ta chi tiet buoc nay lam gi",
      "depends_on": []
    }
  ],
  "dependencies": {
    "step_2": ["step_1"],
    "step_3": ["step_1", "step_2"]
  },
  "confidence": 0.85,
  "memory_queries": ["tu khoa tim skill tuong tu 1", "tu khoa 2"],
  "estimated_complexity": "simple",
  "data_sources": ["mo ta nguon data can thiet neu co"],
  "risks": ["rui ro tiem an neu co"]
}
"""

PLANNER_USER_TEMPLATE = """
Task tu nguoi dung: {task_input}

Hay tao plan chi tiet theo schema da cho.
"""


CODER_SYSTEM_PROMPT = """
Ban la Coder trong he thong AAF-AIOS.
Nhiem vu: nhan plan va sinh code Python chay trong sandbox bi gioi han.

OUTPUT: Chi tra ve JSON thuan tuy.
Khong giai thich, khong markdown, khong text thua ben ngoai JSON.

JSON SCHEMA BAT BUOC:
{
  "filename": "skill_impl.py",
  "code": "code Python day du o day",
  "test_stubs": [
    "def test_happy_path(): pass",
    "def test_invalid_input(): pass"
  ],
  "dependencies": ["thu vien can thiet"],
  "rationale": "giai thich ngan tai sao thiet ke vay"
}
"""

CODER_USER_TEMPLATE = """
Plan can implement:
{plan_json}

Context tu memory (skill tuong tu da co):
{memory_context}

Hay sinh code Python theo dung constraints va schema da cho.
Uu tien tai su dung pattern tu memory context neu phu hop.
"""


REVIEWER_SYSTEM_PROMPT = """
Ban la Reviewer trong he thong AAF-AIOS.
Nhiem vu: danh gia code Python do Coder sinh ra.

OUTPUT: Chi tra ve JSON thuan tuy.
Khong giai thich, khong markdown, khong text thua ben ngoai JSON.

JSON SCHEMA BAT BUOC:
{
  "verdict": "pass",
  "reason_code": "OK",
  "issues": [],
  "security_flags": [],
  "sandbox_violations": [],
  "suggestions": [],
  "must_fix": []
}
"""

REVIEWER_USER_TEMPLATE = """
Code can review:
{code}

Sandbox policy ap dung:
- network: disabled
- fs_write: disabled
- timeout_s: {timeout}
- allowed_imports: {allowed_imports}

Hay review theo checklist va tra ve verdict JSON.
must_fix: list nhung gi bat buoc sua neu verdict=fail hoac warn.
"""


def build_planner_messages(task_input: str) -> List[dict]:
    return [
        {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": PLANNER_USER_TEMPLATE.format(task_input=task_input),
        },
    ]


def build_coder_messages(
    plan_json: str,
    memory_context: str = "",
) -> List[dict]:
    return [
        {"role": "system", "content": CODER_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": CODER_USER_TEMPLATE.format(
                plan_json=plan_json,
                memory_context=memory_context or "Khong co context tuong tu.",
            ),
        },
    ]


def build_reviewer_messages(
    code: str,
    timeout: int = 30,
    allowed_imports: Optional[list] = None,
) -> List[dict]:
    if allowed_imports is None:
        allowed_imports = [
            "matplotlib",
            "datetime",
            "json",
            "re",
            "math",
            "statistics",
            "base64",
            "io",
            "typing",
            "collections",
            "itertools",
        ]
    return [
        {"role": "system", "content": REVIEWER_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": REVIEWER_USER_TEMPLATE.format(
                code=code,
                timeout=timeout,
                allowed_imports=", ".join(allowed_imports),
            ),
        },
    ]
