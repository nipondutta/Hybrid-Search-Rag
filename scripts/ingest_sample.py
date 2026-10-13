from pathlib import Path
from app.ingestion.chunker import chunk_records
from app.ingestion.loaders import load_document

path = Path("data/sample/technical_docs.txt")
records = load_document(path)
chunks = chunk_records(records)
print(f"Loaded {len(records)} record(s), created {len(chunks)} chunk(s).")
for chunk in chunks:
    print(chunk["chunk_id"], chunk["source"], chunk["text"][:80])
