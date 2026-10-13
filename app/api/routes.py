from pathlib import Path
from tempfile import NamedTemporaryFile
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from app.core.config import get_settings
from app.ingestion.chunker import chunk_records
from app.ingestion.loaders import load_document
from app.retrieval.hybrid import HybridSearch

router = APIRouter()
settings = get_settings()
CHUNKS: list[dict] = []
SEARCH: HybridSearch | None = None

class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    mode: str = Field(default="hybrid", pattern="^(bm25|dense|hybrid)$")
    top_k: int = Field(default=5, ge=1, le=20)

def rebuild_search() -> None:
    global SEARCH
    SEARCH = HybridSearch(CHUNKS) if CHUNKS else None

@router.get("/health")
def health() -> dict:
    return {"status": "ok", "indexed_chunks": len(CHUNKS)}

@router.post("/documents")
async def upload_document(file: UploadFile = File(...)) -> dict:
    global CHUNKS
    filename = Path(file.filename or "upload.txt").name
    suffix = Path(filename).suffix.lower()
    if suffix not in {".txt", ".md", ".pdf"}:
        raise HTTPException(400, "Only .txt, .md, and .pdf files are supported")
    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, "File exceeds configured upload limit")
    try:
        with NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
            tmp.write(content)
            tmp.flush()
            records = load_document(tmp.name)
            for record in records:
                record.update({"source": filename, "title": filename,
                               "document_id": Path(filename).stem})
            new_chunks = chunk_records(records, settings.chunk_size, settings.chunk_overlap)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(400, "Could not parse document") from exc
    existing_ids = {c["chunk_id"] for c in CHUNKS}
    CHUNKS.extend(c for c in new_chunks if c["chunk_id"] not in existing_ids)
    rebuild_search()
    return {"filename": filename, "chunks_added": len(new_chunks), "total_chunks": len(CHUNKS)}

@router.post("/search")
def search(request: SearchRequest) -> dict:
    if SEARCH is None:
        raise HTTPException(400, "No documents indexed. Upload a document first.")
    try:
        results = SEARCH.search(request.query, request.top_k, request.mode)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    safe_results = []
    for rank, result in enumerate(results, start=1):
        safe_results.append({
            "chunk_id": result["chunk_id"], "document_id": result.get("document_id"),
            "title": result.get("title"), "source": result.get("source"),
            "page_number": result.get("page_number"), "text": result["text"],
            "rank": rank, "score": result.get("rrf_score", result.get("retriever_score"))
        })
    return {"query": request.query, "mode": request.mode, "results": safe_results}
