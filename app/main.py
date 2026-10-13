from fastapi import FastAPI
from app.api.routes import router
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name,
              description="Local hybrid search with BM25, FAISS, and Sentence Transformers.",
              version="1.0.0")
app.include_router(router)
