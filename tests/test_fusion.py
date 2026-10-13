from app.retrieval.hybrid import reciprocal_rank_fusion

def test_rrf_promotes_overlap():
    first = [{"chunk_id": "a", "text": "A"}, {"chunk_id": "b", "text": "B"}]
    second = [{"chunk_id": "a", "text": "A"}, {"chunk_id": "c", "text": "C"}]
    results = reciprocal_rank_fusion([first, second])
    assert results[0]["chunk_id"] == "a"

def test_rrf_empty():
    assert reciprocal_rank_fusion([[], []]) == []
