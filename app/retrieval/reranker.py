"""Cross-encoder reranking."""

from functools import lru_cache
from typing import Any

from sentence_transformers import CrossEncoder

from app.config import get_settings


@lru_cache
def get_reranker() -> CrossEncoder | None:
    settings = get_settings()
    try:
        return CrossEncoder(settings.reranker_model)
    except Exception:
        return None


class Reranker:
    def __init__(self):
        self.settings = get_settings()
        self.model = get_reranker()

    def rerank(self, query: str, candidates: list[dict[str, Any]], top_k: int | None = None) -> list[dict[str, Any]]:
        k = top_k or self.settings.top_k_rerank
        if not candidates:
            return []

        if self.model is None:
            return sorted(candidates, key=lambda x: x.get("hybrid_score", 0), reverse=True)[:k]

        pairs = [(query, c.get("text", "")) for c in candidates]
        scores = self.model.predict(pairs)
        for candidate, score in zip(candidates, scores):
            candidate["rerank_score"] = float(score)

        ranked = sorted(candidates, key=lambda x: x.get("rerank_score", 0), reverse=True)
        return ranked[:k]
