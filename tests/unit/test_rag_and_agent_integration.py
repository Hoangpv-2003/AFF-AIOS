from __future__ import annotations

from app.agents.base_agent import AgentContext
from app.agents.coder import CoderAgent
from app.brain.memory import InMemoryVectorStore
from app.brain.planner import PlannerAgent
from app.brain.rag import RAGService


class DeterministicEmbeddingClient:
    def embed(self, text: str) -> list[float]:
        vector = [0.0, 0.0, 0.0, 0.0]
        for index, char in enumerate(text.lower()):
            vector[index % 4] += float(ord(char) % 29)
        norm = sum(abs(value) for value in vector) or 1.0
        return [value / norm for value in vector]


class StubLLM:
    def __init__(self, response: str) -> None:
        self.response = response

    def generate(self, prompt: str, system_prompt: str | None = None, model: str | None = None) -> str:
        del prompt, system_prompt, model
        return self.response


def _build_context(task_id: str, prompt: str) -> AgentContext:
    return AgentContext(task_id=task_id, trace_id=f"trace-{task_id}", prompt=prompt)


def test_rag_service_ingest_and_build_context_returns_hits():
    rag = RAGService(
        vector_store=InMemoryVectorStore(),
        embedding_client=DeterministicEmbeddingClient(),
    )
    rag.ingest("m1", "build auth endpoint and unit tests", {"type": "note"})

    context = rag.build_context("auth endpoint", top_k=1)

    assert "auth endpoint" in context.lower()


def test_planner_uses_llm_and_persists_plan_to_rag():
    rag = RAGService(
        vector_store=InMemoryVectorStore(),
        embedding_client=DeterministicEmbeddingClient(),
    )
    rag.ingest("seed", "existing memory about auth", {"type": "seed"})

    planner = PlannerAgent(
        llm_client=StubLLM("design API\nimplement endpoint\nwrite tests"),
        rag_service=rag,
    )
    result = planner.act(_build_context("t-plan", "create auth API"), {"prompt": "create auth API"})

    assert result.success is True
    plan = (result.payload or {}).get("plan", {})
    assert plan.get("steps")[:2] == ["design API", "implement endpoint"]

    remembered = rag.build_context("create auth API", top_k=5)
    assert "task=create auth api" in remembered.lower()


def test_coder_uses_llm_rationale_and_persists_summary():
    rag = RAGService(
        vector_store=InMemoryVectorStore(),
        embedding_client=DeterministicEmbeddingClient(),
    )
    rag.ingest("seed", "memory about code style", {"type": "seed"})

    coder = CoderAgent(
        llm_client=StubLLM("Artifacts match the objective and include tests."),
        rag_service=rag,
    )
    plan = {
        "objective": "Implement login flow",
        "steps": ["create endpoint", "add tests"],
        "confidence": 0.9,
    }

    result = coder.act(_build_context("t-code", "Implement login flow"), {"plan": plan, "memory_hits": []})

    assert result.success is True
    artifacts = (result.payload or {}).get("artifacts", {})
    assert "artifacts match the objective" in artifacts.get("rationale", "").lower()

    remembered = rag.build_context("Implement login flow", top_k=5)
    assert "objective=implement login flow" in remembered.lower()
