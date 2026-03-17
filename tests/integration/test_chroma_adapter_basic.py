from app.brain.memory import MemoryQuery, MemoryRecord
from app.infrastructure.database.chroma_store import ChromaMemoryStore


def test_chroma_adapter_basic_flow():
    store = ChromaMemoryStore(collection_name="test-memory")
    store.upsert(
        [
            MemoryRecord(id="a", text="sandbox offline policy", embedding=[0.9, 0.1]),
            MemoryRecord(id="b", text="queue latency policy", embedding=[0.1, 0.9]),
        ]
    )

    results = store.search(MemoryQuery(query_text="sandbox", embedding=[1.0, 0.0], top_k=1))
    assert len(results) == 1
    assert results[0].record.id == "a"

    deleted = store.delete(["a"])
    assert deleted == 1

    health = store.health()
    assert health["backend"] == "chroma_adapter_local"
