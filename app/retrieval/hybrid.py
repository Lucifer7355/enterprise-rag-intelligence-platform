"""Hybrid retrieval combining dense and sparse scores."""

from typing import Any

from app.config import get_settings
from app.storage.elasticsearch_store import ElasticsearchStore
from app.storage.qdrant_store import QdrantStore


def reciprocal_rank_fusion(
    dense_results: list[dict],
    sparse_results: list[dict],
    semantic_weight: float,
    bm25_weight: float,
    k: int = 60,
) -> list[dict[str, Any]]:
    """Combine rankings using weighted RRF-style fusion."""
    scores: dict[str, float] = {}
    meta: dict[str, dict] = {}

    for rank, item in enumerate(dense_results):
        cid = item["chunk_id"]
        scores[cid] = scores.get(cid, 0) + semantic_weight / (k + rank + 1)
        meta[cid] = item

    for rank, item in enumerate(sparse_results):
        cid = item["chunk_id"]
        scores[cid] = scores.get(cid, 0) + bm25_weight / (k + rank + 1)
        meta[cid] = item

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [
        {**meta[cid], "hybrid_score": score}
        for cid, score in ranked
    ]


class HybridRetriever:
    def __init__(self):
        self.settings = get_settings()
        self.qdrant = QdrantStore()
        self.es = ElasticsearchStore()

    def retrieve(self, query: str, role: str, top_k: int | None = None) -> list[dict[str, Any]]:
        k = top_k or self.settings.top_k_retrieval
        dense = self.qdrant.search(query, role, top_k=k)
        sparse = self.es.search(query, role, top_k=k)
        return reciprocal_rank_fusion(
            dense,
            sparse,
            self.settings.hybrid_semantic_weight,
            self.settings.hybrid_bm25_weight,
        )[:k]
