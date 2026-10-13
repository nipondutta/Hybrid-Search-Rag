# Full Step-by-Step Project and Deployment Guide

## Phase 1 — Environment
Install Python 3.12, create a virtual environment, install `requirements.txt`, and run `pytest` and `ruff check .`.

## Phase 2 — Ingestion
`app/ingestion/loaders.py` supports TXT, Markdown, and PDF. `chunker.py` normalizes text and splits it into overlapping character windows. Inspect chunks and tune chunk size/overlap for your documents.

## Phase 3 — BM25
`app/retrieval/bm25.py` tokenizes query and document text and ranks with `rank-bm25`. Validate exact error codes, product IDs and technical terms.

## Phase 4 — Dense retrieval
`app/embeddings/model.py` loads `all-MiniLM-L6-v2`. The first run downloads the model. `app/retrieval/dense.py` builds a FAISS flat inner-product index using normalized vectors.

## Phase 5 — Hybrid fusion
`app/retrieval/hybrid.py` runs both retrievers and combines rankings with Reciprocal Rank Fusion. Compare all three modes on identical queries.

## Phase 6 — API
Run `uvicorn app.main:app --reload`. Use `/docs` to upload a file and search. Endpoints: `GET /health`, `POST /documents`, `POST /search`.

## Phase 7 — Testing and quality
Run `pytest` and `ruff check .`. Add labelled evaluation queries and measure Recall@k, MRR, nDCG and latency. Do not report invented performance numbers.

## Phase 8 — Docker
Install Docker Desktop/Engine and run `docker compose up --build`. Check `/health` and `/docs`; stop with `docker compose down`. The index is currently in memory and will reset after restart.

## Phase 9 — GitHub CI
Push to GitHub. The workflow at `.github/workflows/ci.yml` runs lint, tests and a Docker build. GitHub Actions usage is subject to plan limits.

## Phase 10 — AWS (optional, not needed for the free version)
Skip this phase if you need to keep the project at zero cost. AWS resources can incur charges.

1. Review current pricing and configure budget alerts.
2. Create an ECR repository.
3. Choose how to host search. A FAISS index requires durable storage and a strategy for updates/rebuilds; do not depend on ephemeral ECS storage.
4. Create an ECS Fargate service and least-privilege task roles.
5. Configure private networking; expose the API via HTTPS if public access is needed.
6. Use S3 for original documents and appropriate durable storage for metadata/index artifacts.
7. Configure CloudWatch logs and alarms.
8. Configure GitHub OIDC with restricted trust and permissions; avoid long-lived AWS keys.
9. Add a separate deploy workflow to publish a commit-SHA-tagged image, update the ECS task definition, deploy, wait for stability and run a health check.
10. Verify monitoring, authentication, rollback and resource cleanup.

## Production gaps
Before public production use, implement durable indexing, authentication/authorization, rate limits, upload validation, safe error responses, monitoring, backup/reindexing, dependency scanning and an operational rollback plan.
