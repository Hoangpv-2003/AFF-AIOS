from app.brain.memory import InMemoryVectorStore, MemoryQuery, MemoryRecord


def test_memory_store_upsert_search_delete_contract():
    store = InMemoryVectorStore()
    records = [
        MemoryRecord(id="1", text="build auth endpoint", embedding=[1.0, 0.0]),
        MemoryRecord(id="2", text="create tracing middleware", embedding=[0.0, 1.0]),
    ]

    store.upsert(records)
    results = store.search(MemoryQuery(query_text="auth", top_k=1, embedding=[1.0, 0.0]))

    assert len(results) == 1
    assert results[0].record.id == "1"

    deleted = store.delete(["1"])
    assert deleted == 1

    health = store.health()
    assert health["status"] == "ok"
