from app.retrieval.bm25 import BM25Retriever
from app.retrieval.dense import DenseRetriever

def reciprocal_rank_fusion(ranked_lists: list[list[dict]], k: int = 60) -> list[dict]:
    """Fuse by chunk_id. RRF scores are ranking scores, not probabilities."""
    fused = {}
    for results in ranked_lists:
        seen = set()
        for rank, result in enumerate(results, start=1):
            cid = result["chunk_id"]
            if cid in seen:
                continue
            seen.add(cid)
            if cid not in fused:
                fused[cid] = {**result, "rrf_score": 0.0}
            fused[cid]["rrf_score"] += 1.0 / (k + rank)
    return sorted(fused.values(), key=lambda item: item["rrf_score"], reverse=True)

class HybridSearch:
    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        self.bm25 = BM25Retriever(chunks)
        self.dense = DenseRetriever(chunks)

    def search(self, query: str, top_k: int = 5, mode: str = "hybrid") -> list[dict]:
        if not 1 <= top_k <= 50:
            raise ValueError("top_k must be between 1 and 50")
        if mode == "bm25":
            return self.bm25.search(query, top_k)
        if mode == "dense":
            return self.dense.search(query, top_k)
        if mode != "hybrid":
            raise ValueError("mode must be bm25, dense, or hybrid")
        candidate_k = min(max(top_k * 3, 10), max(len(self.chunks), 1))
        return reciprocal_rank_fusion([
            self.bm25.search(query, candidate_k),
            self.dense.search(query, candidate_k)
        ])[:top_k]
