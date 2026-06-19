"""Unified tracing: OpenTelemetry + Langfuse + Phoenix."""

from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter

from opentelemetry import trace

from app.observability.langfuse_client import end_span, start_span, start_trace

tracer = trace.get_tracer("enterprise-rag")
_active_langfuse_trace = None


def set_active_trace(trace_obj) -> None:
    global _active_langfuse_trace
    _active_langfuse_trace = trace_obj


@contextmanager
def trace_span(name: str, attributes: dict | None = None):
    start = perf_counter()
    lf_span = start_span(_active_langfuse_trace, name, attributes)

    with tracer.start_as_current_span(name) as span:
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, str(v))
        try:
            yield span
        finally:
            elapsed_ms = (perf_counter() - start) * 1000
            span.set_attribute("duration_ms", elapsed_ms)
            end_span(lf_span, {"duration_ms": elapsed_ms})


@contextmanager
def trace_request(name: str, user_id: str | None = None, metadata: dict | None = None):
    global _active_langfuse_trace
    lf_trace = start_trace(name, user_id=user_id, metadata=metadata)
    _active_langfuse_trace = lf_trace
    try:
        with trace_span(name, metadata):
            yield lf_trace
    finally:
        _active_langfuse_trace = None
