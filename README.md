# Hybrid Search RAG

A lightweight retrieval system that combines lexical search and semantic search to answer document queries from local files. The project is intentionally simple and portable: it stores chunks in memory, builds a BM25 index and a FAISS vector index, and exposes them through a FastAPI service.

This is a retrieval-first system, not a generative chatbot. It helps you search uploaded documents by keyword, semantic similarity, or a hybrid of both. You can use it as a starter project for RAG experimentation, internal knowledge search, or a learning playground for search engineering.

## What this project does

- Accepts `.txt`, `.md`, and `.pdf` uploads
- Extracts text from files and splits it into overlapping chunks
- Builds a BM25 (lexical) index for exact or fuzzy keyword matching
- Builds a dense vector index using Sentence Transformers embeddings and FAISS
- Fuses results from both retrievers using Reciprocal Rank Fusion (RRF)
- Exposes a searchable API with health, upload, and search endpoints
- Runs locally with Python and Docker
- Includes tests and linting in CI

## Why hybrid search

A single retrieval method often misses relevant results:

- BM25 is strong for exact keyword matches and technical terms
- Dense vector search is better for semantic similarity and paraphrasing
- Hybrid retrieval combines the strengths of both

This project uses RRF to merge rankings from both systems and return a single, ordered result list.

## Architecture overview

The application flow is intentionally straightforward:

1. Documents are loaded from disk or uploaded through the API.
2. Text is normalized and chunked into overlapping segments.
3. A BM25 index is built over cleaned tokenized text.
4. Sentence-transformer embeddings are generated for chunk text.
5. FAISS stores normalized vectors and supports nearest-neighbor search.
6. Search requests route to one of three modes:
   - `bm25`: lexical search only
   - `dense`: semantic search only
   - `hybrid`: lexical + semantic fusion via RRF
7. Results are returned as ranked chunks with metadata such as file name, page number, and chunk text.

## Tech stack

- Python 3.12
- FastAPI for the API layer
- Pydantic for request validation
- rank-bm25 for lexical retrieval
- SentenceTransformers for embeddings
- FAISS CPU for vector search
- PyMuPDF for PDF extraction
- pytest for tests
- Ruff for linting
- Docker and Docker Compose for containerized runtime

## Project structure

```text
.
├── app/
│   ├── api/
│   │   └── routes.py          # API endpoints and request validation
│   ├── core/
│   │   └── config.py          # Application settings
│   ├── embeddings/
│   │   └── model.py           # Embedding model loader and encoder
│   ├── ingestion/
│   │   ├── chunker.py         # Text cleaning and chunk creation
│   │   └── loaders.py         # TXT/MD/PDF extraction
│   ├── retrieval/
│   │   ├── bm25.py            # Lexical retriever
│   │   ├── dense.py           # Dense vector retriever
│   │   └── hybrid.py          # RRF-based fusion logic
│   ├── main.py                # FastAPI app bootstrap
│   └── __init__.py
├── data/
│   └── sample/
│       └── technical_docs.txt # Example document set for local testing
├── tests/
│   └── test_api.py            # Basic health check tests
├── .github/workflows/
│   └── ci.yml                 # GitHub Actions CI
├── .env.example               # Example environment settings
├── compose.yaml               # Docker Compose setup
├── Dockerfile                 # Container image definition
├── requirements.txt           # Python dependencies
├── pyproject.toml             # Ruff and pytest config
├── scripts/
│   └── ingest_sample.py      # Quick sample ingestion script
├── README.md                  # Project documentation
```

## Requirements

Before running the app, make sure you have:

- Python 3.12 recommended
- pip or another package installer
- Internet access for the initial model download
- Docker Desktop or Docker Engine if you want to run the containerized version

## Local setup

### 1) Create and activate a virtual environment

On Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

If PowerShell blocks script execution, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment again.

### 2) Install dependencies

```powershell
pip install -r requirements.txt
```

### 3) Run tests and linting

```powershell
pytest
ruff check .
```

### 4) Start the app

```powershell
uvicorn app.main:app --reload
```

The app will run at:

- API: http://127.0.0.1:8000
- Swagger docs: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Sample ingestion

This project includes a small sample document set in `data/sample/technical_docs.txt`.

You can load it directly with:

```powershell
python -m scripts.ingest_sample
```

This script reads the sample file, chunks it, and prints generated chunk IDs and the first part of each chunk to confirm ingestion works.

## API usage

The app exposes three main endpoints:

### Health check

```http
GET /health
```

Example response:

```json
{
  "status": "ok",
  "indexed_chunks": 0
}
```

### Upload a document

```http
POST /documents
```

This accepts a multipart file upload named `file` and only supports:

- `.txt`
- `.md`
- `.pdf`

Example with `curl`:

```powershell
curl -X POST "http://127.0.0.1:8000/documents" -F "file=@data/sample/technical_docs.txt"
```

Example response:

```json
{
  "filename": "technical_docs.txt",
  "chunks_added": 23,
  "total_chunks": 23
}
```

### Search

```http
POST /search
```

Request body:

```json
{
  "query": "Why does the API gateway time out?",
  "mode": "hybrid",
  "top_k": 5
}
```

Supported modes:

- `bm25` — keyword-based lexical search
- `dense` — semantic vector search
- `hybrid` — combined ranking via RRF

Example response:

```json
{
  "query": "Why does the API gateway time out?",
  "mode": "hybrid",
  "results": [
    {
      "chunk_id": "4b5d8f3f2b4ec9a3",
      "document_id": "technical_docs",
      "title": "technical_docs.txt",
      "source": "technical_docs.txt",
      "page_number": null,
      "text": "An HTTP 504 Gateway Timeout occurs when a gateway does not receive a timely response from an upstream server...",
      "rank": 1,
      "score": 0.5312
    }
  ]
}
```

## Search behavior and ranking

The core retrieval logic works like this:

### BM25 lexical retrieval

- Tokenizes text using regex over letters, numbers, periods, and hyphenated words
- Lowercases the text
- Creates a BM25 index from chunk text
- Ranks chunks by query term importance

This is useful for exact matches such as `timeout`, `401`, or `rate limit`.

### Dense semantic retrieval

- Encodes each chunk into a vector using `sentence-transformers/all-MiniLM-L6-v2`
- Normalizes embeddings
- Uses FAISS `IndexFlatIP` for inner-product search
- Searches by embedding similarity to the query

This is useful for conceptual matching when the user asks with different terminology.

### Hybrid merging with RRF

The hybrid mode runs both retrievers and combines their rankings using reciprocal rank fusion:

```text
RRF_score = sum(1 / (k + rank))
```

where:

- `k` is a constant (default is 60 in the project)
- `rank` is the position of the document in each retriever's ranked list

This method is simple, efficient, and works well when combining search systems with different strengths.

## Configuration

Settings are loaded from the environment and `.env` files through `pydantic-settings`.

The default values are defined in `app/core/config.py`:

```python
app_name = "Hybrid Search RAG"
embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
chunk_size = 900
chunk_overlap = 150
default_top_k = 5
max_upload_mb = 10
```

You can override them with environment variables or a `.env` file based on `.env.example`.

Example `.env`:

```env
APP_NAME=Hybrid Search RAG
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=900
CHUNK_OVERLAP=150
DEFAULT_TOP_K=5
MAX_UPLOAD_MB=10
DATA_DIR=data
```

## Docker

The repository includes a Dockerfile and Compose setup for a containerized run.

### Run with Docker Compose

```powershell
docker compose up --build
```

Then open:

- http://127.0.0.1:8000/docs

To stop the container:

```powershell
docker compose down
```

### Notes

- The first run will download the embedding model and may take a little time.
- Uploaded files are kept in process memory for the current runtime only.
- Restarting the container clears the in-memory indexes.

## CI and automation

The GitHub Actions workflow in `.github/workflows/ci.yml` runs linting and tests automatically when changes are pushed or pull requests are opened.

The workflow is intended to validate basic correctness and project health before merging.

## Limitations

This project is useful as a learning and prototyping tool, but it is not production-ready in its current form.

Current limitations include:

- In-memory indexing is lost on restart
- No authentication or authorization layer
- No rate limiting or abuse protection
- No persistent storage for index artifacts or uploaded documents
- No OCR support for scanned PDFs
- No document update/delete/reindex workflow
- Simple character-based chunking is not optimized for all content types
- Upload validation is lightweight and intended for local experimentation

## Production-minded improvements

If you want to turn this into a robust application, these are the next logical improvements:

1. Persist FAISS indexes and metadata to disk or object storage
2. Add document update, delete, and reindex operations
3. Add token-aware chunking and better metadata pruning
4. Add user authentication and authorization
5. Add rate limiting and request validation
6. Add evaluation metrics such as Recall@k, MRR, nDCG, and latency tracking
7. Add citations and answer-generation on top of the retrieval layer
8. Add a proper database and background jobs for ingestion and indexing
9. Pin dependencies and CI actions to a verified software supply chain

## Troubleshooting

### The model download is slow

This is expected on the first run. The project downloads `sentence-transformers/all-MiniLM-L6-v2` locally. Subsequent runs should be much faster.

### PowerShell activation fails

Use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then rerun the activation command.

### Search returns no results

Check that:

- the document was uploaded successfully
- the app is still running
- the request body uses a valid `mode` and `top_k`
- the file contains extractable text

### Docker image takes a long time to build

The main cost is dependency installation and model setup. Building once and then reusing the image helps with subsequent runs.

## Summary

This repository is a compact, practical hybrid search project built with Python and local ML tooling. It demonstrates the core ideas behind enterprise-style retrieval systems without depending on cloud services or a hosted vector database.

It is a strong foundation for:

- learning retrieval-system design
- experimenting with BM25 + vector hybrid search
- building document search into internal tools
- expanding into a RAG or knowledge assistant architecture

If you want to extend it further, the next natural step is to add persistent storage, a richer document ingestion pipeline, and an LLM layer on top of the retrieval stack.
