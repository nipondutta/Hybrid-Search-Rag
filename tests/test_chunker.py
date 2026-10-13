import pytest
from app.ingestion.chunker import chunk_records

def test_chunker_overlap():
    records = [{"document_id": "a", "text": "abcdefghij", "source": "a.txt"}]
    chunks = chunk_records(records, chunk_size=6, overlap=2)
    assert [c["text"] for c in chunks] == ["abcdef", "efghij"]

def test_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_records([{"text": "hello"}], chunk_size=10, overlap=10)
