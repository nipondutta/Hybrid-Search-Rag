import faiss
import numpy as np
from app.embeddings.model import embed_texts

class DenseRetriever:
    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        self.index = None
        if chunks:
            vectors = embed_texts([c["text"] for c in chunks])
            self.index = faiss.IndexFlatIP(vectors.shape[1])
            self.index.add(np.ascontiguousarray(vectors, dtype="float32"))

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if not query.strip() or not self.chunks or self.index is None:
            return []
        vector = embed_texts([query])
        scores, indices = self.index.search(
            np.ascontiguousarray(vector, dtype="float32"), min(top_k, len(self.chunks)))
        results = []
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0]), start=1):
            if idx >= 0:
                results.append({**self.chunks[int(idx)], "retriever": "dense",
                                "retriever_rank": rank, "retriever_score": float(score)})
        return results
