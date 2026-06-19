"""Retrieval and generation evaluation framework."""

import math
from typing import Any

from app.config import get_settings
from app.evaluation.ragas_evaluator import run_live_ragas
from app.models.schemas import EvaluateResponse
from app.observability.audit import audit_logger
from app.retrieval.hybrid import HybridRetriever

DEFAULT_TEST_QUERIES = [
    {
        "query": "Show failed payment incidents from last week",
        "relevant_chunk_ids": [],
        "role": "Engineering",
    },
    {
        "query": "What are the compliance violations for Team Alpha?",
        "relevant_chunk_ids": [],
        "role": "Compliance",
    },
    {
        "query": "Monthly infrastructure expenses",
        "relevant_chunk_ids": [],
        "role": "Finance",
    },
]


class EvaluationFramework:
    def __init__(self):
        self.retriever = HybridRetriever()
        self.settings = get_settings()

    def recall_at_k(self, retrieved: list[str], relevant: set[str], k: int) -> float:
        if not relevant:
            return 1.0
        top_k = set(retrieved[:k])
        return len(top_k & relevant) / len(relevant)

    def precision_at_k(self, retrieved: list[str], relevant: set[str], k: int) -> float:
        top_k = retrieved[:k]
        if not top_k:
            return 0.0
        return len(set(top_k) & relevant) / len(top_k)

    def mrr(self, retrieved: list[str], relevant: set[str]) -> float:
        for i, doc in enumerate(retrieved):
            if doc in relevant:
                return 1.0 / (i + 1)
        return 0.0

    def ndcg_at_k(self, retrieved: list[str], relevant: set[str], k: int) -> float:
        dcg = sum(1.0 / math.log2(i + 2) for i, doc in enumerate(retrieved[:k]) if doc in relevant)
        ideal = sum(1.0 / math.log2(i + 2) for i in range(min(len(relevant), k)))
        return dcg / ideal if ideal > 0 else 0.0

    def run(self, test_queries: list[dict[str, Any]] | None = None) -> EvaluateResponse:
        queries = test_queries or DEFAULT_TEST_QUERIES
        k = 5
        recalls, precisions, mrrs, ndcgs = [], [], [], []

        for tq in queries:
            role = tq.get("role", "Engineering")
            results = self.retriever.retrieve(tq["query"], role, top_k=k)
            retrieved_ids = [r["chunk_id"] for r in results]
            relevant = set(tq.get("relevant_chunk_ids", []))

            recalls.append(self.recall_at_k(retrieved_ids, relevant, k))
            precisions.append(self.precision_at_k(retrieved_ids, relevant, k))
            mrrs.append(self.mrr(retrieved_ids, relevant))
            ndcgs.append(self.ndcg_at_k(retrieved_ids, relevant, k))

        n = len(queries) or 1
        security = audit_logger.security_stats()
        generation = run_live_ragas()

        return EvaluateResponse(
            retrieval_metrics={
                "recall_at_k": round(sum(recalls) / n, 4),
                "precision_at_k": round(sum(precisions) / n, 4),
                "mrr": round(sum(mrrs) / n, 4),
                "ndcg": round(sum(ndcgs) / n, 4),
            },
            generation_metrics={
                "faithfulness": generation.get("faithfulness", 0.0),
                "answer_relevance": generation.get("answer_relevance", 0.0),
                "context_precision": generation.get("context_precision", 0.0),
            },
            security_metrics=security,
            evaluation_method=generation.get("method", "unknown"),
        )
