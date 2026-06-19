"""Unit tests for config-driven query classification."""

from app.retrieval.classifier import classify_query_keyword


def test_incident_classification():
    assert classify_query_keyword("Show failed payment incidents") == "Incident Query"


def test_compliance_classification():
    assert classify_query_keyword("compliance violations Team Alpha") == "Compliance Query"


def test_financial_classification():
    assert classify_query_keyword("monthly revenue report") == "Financial Query"
