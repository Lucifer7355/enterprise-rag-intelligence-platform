"""Unit tests for live RAGAS evaluation."""

from app.evaluation.ragas_evaluator import (
    _heuristic_faithfulness,
    _heuristic_relevance,
    run_live_ragas,
)


def test_heuristic_faithfulness():
    score = _heuristic_faithfulness(
        "payment incidents from payment-api",
        ["Incident INC-001 Service: payment-api Severity: ERROR"],
    )
    assert score > 0.3


def test_heuristic_relevance():
    score = _heuristic_relevance("payment incidents occurred", "show payment incidents")
    assert score > 0.0


def test_run_live_ragas():
    result = run_live_ragas()
    assert "faithfulness" in result
    assert "answer_relevance" in result
    assert "context_precision" in result
    assert result["method"] in ("heuristic_live", "ragas_live")
