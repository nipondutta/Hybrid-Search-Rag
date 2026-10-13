from functools import lru_cache
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import get_settings

@lru_cache
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(get_settings().embedding_model)

def embed_texts(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.empty((0, 0), dtype="float32")
    vectors = get_embedding_model().encode(texts, convert_to_numpy=True,
        normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(vectors, dtype="float32")
