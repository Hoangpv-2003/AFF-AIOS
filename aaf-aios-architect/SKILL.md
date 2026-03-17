---
name: aaf-aios-architect
description: Provides the reference architecture, key components, roadmap, and operating principles for the AAF-AIOS project. Use this skill whenever you need to understand the project structure, how the different agents interact, what phase of the roadmap we are in, or how the self-learning and tracing loops are implemented. Trigger this if the user asks about the overall system design, where files should be placed, or how to expand the system's capabilities.
---

# AAF-AIOS Architect Skill

This skill documents the structure, philosophy, and features of the AAF-AIOS (Autonomous Agentic Framework - Artificial Intelligence Operating System) project.

## 1. Core Principles

AAF-AIOS is a Multi-Agent system focused on giving LLMs deep autonomy. It features:
- **Dynamic Planning**: Decomposing high-level tasks into actionable sub-tasks.
- **Auto-Skill Generation**: Automatically writing and integrating new Python functions when missing capabilities.
- **Self-Learning**: Storing past successes (Context + Code) in a Vector DB via a RAG lookup before undertaking new coding tasks.
- **Auto-Tracing**: Emphasizing extreme observability where every Thought, Action, and Observation is logged and tied to a `trace_id`.

## 2. Directory Structure (Clean Architecture x DDD)

The project enforces strict separation of concerns via Clean Architecture.

```text
project-root/
├── app/
│   ├── api/                # The REST API entrypoints, Routers, Dependencies
│   ├── core/               # Global config (DB, Auth, LLM settings, Security)
│   ├── agents/             # Agent implementations (Manager, Coder, Reviewer, Planner)
│   ├── brain/              # System memory (RAG), Reasoning Prompts, Planning logic
│   ├── skills/             # Where the auto-generated code lands (dynamic/ and static/) along with registry
│   ├── infrastructure/     # Database connections, third-party External APIs, isolated Sandboxes
│   └── schemas/            # Pydantic data validation
├── logs/                   # Subsystem trace outputs
├── tests/                  # Tests encompassing Core Logic + Sandbox logic
├── requirements.txt
└── docker-compose.yml
```

When building new features, respect these boundaries. E.g., Database connections do not go into `app/api`; they belong in `app/infrastructure`.

## 3. The Auto-Mechanisms

### A. Auto-Skill Generation (The Coder-Reviewer Loop)
1. The **Manager** agent realizes a tool is missing in `skills/registry.py`.
2. The **Manager** delegates to the **Coder** agent to write a Python script.
3. The **Reviewer** agent tests the script securely in `infrastructure/sandboxes`.
4. If successful, the script is saved to `skills/dynamic/` and the registry is updated.

### B. Self-Learning Loop
Leverages Retrieval-Augmented Generation (RAG).
- **On Success**: The task's `{Requirement, Solution Approach, Code}` is embedded and saved to Vector DB (e.g., Pinecone/Milvus).
- **On Next Task**: The **Manager** / **Coder** agent queries the DB to find similar solved problems and reuses the patterns.

### C. Auto-Tracing
Uses tools analogous to OpenTelemetry / LangSmith.
- Every API request creates a Root Span (`trace_id`).
- Every agent step logs `Thought` (intent), `Action` (tool call), and `Observation` (result) attached to that trace.

## 4. Key Endpoints

For RESTful integration:
- `POST /api/v1/tasks`: Submit a new high-level job.
- `GET /api/v1/tasks/{id}`: Poll for real-time status (Planning, Executing, Success).
- `GET /api/v1/skills`: List dynamically and statically available tools.
- `POST /api/v1/skills/validate`: Human-in-the-loop endpoint to explicitly approve newly generated skills.
- `GET /api/v1/traces/{task_id}`: Fetch the Chain-of-Thought logs.

## 5. Development Roadmap Reference

Check the `ROADMAP.md` in the root directory for specific phase checkpoints mapping to the capabilities listed above. The phases generally follow: Core/API -> Brain/Agents -> Auto-Skill/Self-Learning -> Tracing/Optimization.
