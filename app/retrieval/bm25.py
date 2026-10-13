import re
from rank_bm25 import BM25Okapi

def tokenize(text: str) -> list[str]:
    return re.findall(r"\b[\w.-]+\b", text.lower())

class BM25Retriever:
    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        corpus = [tokenize(f"{c.get('title', '')} {c['text']}") for c in chunks]
        self.index = BM25Okapi(corpus) if corpus else None

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if not query.strip() or not self.chunks or self.index is None:
            return []
        scores = self.index.get_scores(tokenize(query))
        order = sorted(range(len(scores)), key=lambda i: float(scores[i]), reverse=True)
        results = []
        for rank, idx in enumerate(order[:top_k], start=1):
            if float(scores[idx]) <= 0:
                continue
            results.append({**self.chunks[idx], "retriever": "bm25",
                            "retriever_rank": rank, "retriever_score": float(scores[idx])})
        return results
