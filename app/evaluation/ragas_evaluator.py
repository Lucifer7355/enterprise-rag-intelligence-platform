"""Live RAGAS evaluation for generation quality metrics."""

from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.observability.logging import get_logger
from app.retrieval.pipeline import RetrievalPipeline

logger = get_logger(__name__)

EVAL_QUERIES = [
    {
        "query": "Show failed payment incidents",
        "role": "Admin",
        "ground_truth": "Payment-api incidents include transaction timeouts and errors owned by Team Alpha.",
    },
    {
        "query": "What are monthly infrastructure expenses?",
        "role": "Finance",
        "ground_truth": "Infrastructure expenses are listed in monthly_expenses.csv for Engineering department.",
    },
    {
        "query": "Which compliance violations relate to Team Alpha?",
        "role": "Compliance",
        "ground_truth": "Team Alpha systems had compliance violations related to payment-api and data access.",
    },
]


def _heuristic_faithfulness(answer: str, contexts: list[str]) -> float:
    if not answer or "could not find" in answer.lower():
        return 0.0
    if not contexts:
        return 0.3
    answer_words = set(answer.lower().split())
    context_words = set(" ".join(contexts).lower().split())
    overlap = len(answer_words & context_words)
    return min(1.0, overlap / max(len(answer_words), 1) * 2)


def _heuristic_relevance(answer: str, question: str) -> float:
    if not answer:
        return 0.0
    q_words = set(question.lower().split())
    a_words = set(answer.lower().split())
    return min(1.0, len(q_words & a_words) / max(len(q_words), 1) * 1.5)


def _heuristic_context_precision(contexts: list[str], question: str) -> float:
    if not contexts:
        return 0.0
    q_words = set(question.lower().split())
    scores = []
    for ctx in contexts:
        ctx_words = set(ctx.lower().split())
        scores.append(len(q_words & ctx_words) / max(len(q_words), 1))
    return min(1.0, sum(scores) / len(scores))


def run_live_ragas(test_queries: list[dict[str, Any]] | None = None) -> dict[str, float]:
    """Run live RAGAS or heuristic fallback."""
    settings = get_settings()
    queries = test_queries or EVAL_QUERIES
    pipeline = RetrievalPipeline()

    questions, answers, contexts_list, ground_truths = [], [], [], []

    for tq in queries:
        resp = pipeline.process(tq["query"], "eval_user", tq.get("role", "Admin"))
        ctx = [s.snippet for s in resp.sources if s.snippet]
        questions.append(tq["query"])
        answers.append(resp.answer)
        contexts_list.append(ctx if ctx else ["No context retrieved"])
        ground_truths.append(tq.get("ground_truth", ""))

    if not settings.use_mock_llm and settings.openai_api_key:
        try:
            return _run_ragas_llm(questions, answers, contexts_list, ground_truths)
        except Exception as e:
            logger.warning("ragas_llm_failed", error=str(e))

    return _run_heuristic(questions, answers, contexts_list)


def _run_heuristic(questions: list, answers: list, contexts_list: list) -> dict[str, float]:
    faith, rel, prec = [], [], []
    for q, a, ctx in zip(questions, answers, contexts_list):
        faith.append(_heuristic_faithfulness(a, ctx))
        rel.append(_heuristic_relevance(a, q))
        prec.append(_heuristic_context_precision(ctx, q))

    n = len(questions) or 1
    return {
        "faithfulness": round(sum(faith) / n, 4),
        "answer_relevance": round(sum(rel) / n, 4),
        "context_precision": round(sum(prec) / n, 4),
        "method": "heuristic_live",
    }


def _run_ragas_llm(
    questions: list, answers: list, contexts_list: list, ground_truths: list
) -> dict[str, float]:
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import answer_relevancy, context_precision, faithfulness

    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts_list,
        "ground_truth": ground_truths,
    })

    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision],
    )

    df = result.to_pandas()
    return {
        "faithfulness": round(float(df["faithfulness"].mean()), 4),
        "answer_relevance": round(float(df["answer_relevancy"].mean()), 4),
        "context_precision": round(float(df["context_precision"].mean()), 4),
        "method": "ragas_live",
    }
