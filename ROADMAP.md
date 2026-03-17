# The Autonomous Agentic Framework (AAF) - Roadmap
Dự án: **AAF - AIOS** (Artificial Intelligence Operating System)
Mục tiêu: Xây dựng hệ thống đa tác nhân (Multi-agent) có khả năng:
- **Dynamic Planning**: Tự động chia nhỏ nhiệm vụ phức tạp thành nhiều sub-tasks.
- **Auto-Skill Generation**: Tự động sinh Python script (Kỹ năng) khi nhận thấy thiếu công cụ để giải quyết bài toán.
- **Self-Learning**: Sử dụng RAG & Vector DB để tái sử dụng cách giải quyết thành công cho những lần tới.
- **Auto-Tracing**: Ghi log chi tiết luồng tư duy (Thought), hành động (Action) và kết quả (Observation) để kiểm thử và tự học.

---

## Giai đoạn 1: Core Foundation & API Layer (Tuần 1-2)
**Mục tiêu**: Xây dựng nền tảng cốt lõi của Kiến trúc Clean Architecture và Domain-Driven Design.
- [ ] Thiết lập Project Structure (đã hoàn thành cơ bản qua scaffolding).
- [ ] Cấu hình **Giao tiếp API** (FastAPI) với các Endpoint chính yếu (`/tasks`, `/agents`, `/skills`, `/traces`).
- [ ] Thiết lập Dependency Injection (Database, LLM API Keys, Authentication).
- [ ] Thiết lập Docker Sandbox cơ bản để chạy và kiểm thử mã động an toàn.

## Giai đoạn 2: Trí Não (Brain) & Tác Nhân (Agents) (Tuần 3-4)
**Mục tiêu**: Định nghĩa các lớp Agent và cơ chế tư duy (Reasoning) để thực hiện công việc.
- [ ] Xây dựng **Planner Agent**: Phân tích yêu cầu tự nhiên (Natural Language) thành Sub-tasks (Plan).
- [ ] Xây dựng **Coder Agent**: Chuyên trách viết mã Python (Skill Generator).
- [ ] Xây dựng **Reviewer Agent**: Thẩm định mã được viết, chạy Sandbox test.
- [ ] Xây dựng **Manager (Orchestrator)**: Quản trị luồng giao tiếp giữa Planner, Coder, Reviewer.

## Giai đoạn 3: Auto-Skill Generation & Self-Learning (Tuần 5-6)
**Mục tiêu**: Hệ thống có khả năng tự mở rộng chức năng (Skill).
- [ ] Khởi tạo bộ lưu trữ **Vector DB** (Pinecone/Milvus/ChromaDB).
- [ ] Xây dựng quy trình **Auto-Skill Generation**:
    1. Thiếu công cụ -> Coder Agent viết Code.
    2. Reviewer chạy script trong Sandbox.
    3. Nếu pass -> Đăng ký vào bảng `skills/registry.py` & lưu vào `skills/dynamic/`.
- [ ] Triển khai **RAG cho Self-Learning**: Lưu trữ `{Context + Code giải quyết}` thành công vào Vector DB; trước khi Coder viết code mới, truy vấn hệ thống RAG để xem có cách làm cũ tương tự hay không.

## Giai đoạn 4: Observability, Tracing & Tối Ưu (Tuần 7-8)
**Mục tiêu**: Hệ thống trong suốt (Transparent), phục vụ dò lỗi và đánh giá chất lượng.
- [ ] Tích hợp **OpenTelemetry** hoặc LangSmith/LangFuse vào tất cả quá trình ra quyết định.
- [ ] Đảm bảo mỗi task chạy đều mapping chuẩn `trace_id` -> `thought` -> `action` -> `observation`.
- [ ] API theo dõi Realtime Task Progress (`GET /api/v1/tasks/{id}`).
- [ ] Hoàn thiện Human-in-the-loop mechanism: API chờ con người duyệt (Approve Skill).
- [ ] Tối ưu hóa hệ thống Prompt, viết Unit Tests cho toàn bộ Core logic.

---

## MVP Scope (Khóa phạm vi)
- In-scope:
  - Một pipeline chính: `task -> plan -> code -> review -> approve -> register`.
  - Single-tenant runtime.
  - API tối thiểu cho `tasks`, `skills`, `approvals`, `traces`.
  - Sandbox chạy được ở chế độ offline.
- Non-goals:
  - Multi-tenant.
  - Auto-approve production skills.
  - Tối ưu cost nâng cao ngoài hard-limit.

## Release Gates
- Gate 1: ADR-001, ADR-003, ADR-005 phải được approve trước code production.
- Gate 2: Spikes có pass/fail số liệu để finalize ADR-002/004/006.
- Gate 3: Contract tests cho API nền phải pass.
- Gate 4: Control-plane tests (approval, sandbox, budget, reconciliation) phải có happy-path và failure-path.

## Implementation Status (2026-03-17)
- Test baseline: `39 passed` (`pytest -q`, workspace venv).
- Phase status:
  - Phase 1A/1B/1C: Completed.
  - Phase 2A/2B/2C: Completed.
  - Phase 3A/3B/3C: Completed.
  - Phase 4A/4B/4C: Completed.
  - Phase 5A/5B: Completed.

## Milestone Status (M1-M6)
- M1: Completed (docs baseline and blocking ADR files present, accepted where required).
- M2: Completed (spike scripts runnable, evidence artifacts recorded, ADR-002/004/006 accepted).
- M3: Completed (foundation + draft/stable API + contract tests green).
- M4: Completed (memory adapters + manager robust state machine tests green).
- M5: Completed (registry/approval/reconciliation/sandbox/budget tests green).
- M6: Completed (observability + CI gates + canary simulation implemented and tested).

---

## Kiến trúc Hệ thống (Clean Architecture & DDD)

```text
project-root/
├── app/
│   ├── api/                # RESTful API (v1 endpoints, routers, dependencies)
│   ├── core/               # Configuration, Security, Global Constants
│   ├── agents/             # Manager, Coder, Reviewer, Base Agent
│   ├── brain/              # Planner, Memory (RAG), Reasoning Prompts
│   ├── skills/             # Registry, Dynamic/Static Python skills
│   ├── infrastructure/     # Data & Services (DB, Vector Store, Sandboxes, external APIs)
│   └── schemas/            # Data validation tools (Pydantic/DataClasses)
└── (...)
```
