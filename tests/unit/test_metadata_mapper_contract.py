from app.infrastructure.database.metadata_mapper import normalize_filters


def test_metadata_mapper_normalizes_common_filter_types():
    raw = {
        "owner": "team-a",
        "tags": ["api", "security"],
        "score": {"min": 0.7, "max": 0.95},
        "title": {"contains": "auth"},
    }

    mapped = normalize_filters(raw)

    assert mapped["owner"] == {"op": "eq", "value": "team-a"}
    assert mapped["tags"] == {"op": "in", "values": ["api", "security"]}
    assert mapped["score"] == {"op": "range", "min": 0.7, "max": 0.95}
    assert mapped["title"] == {"op": "contains", "value": "auth"}
