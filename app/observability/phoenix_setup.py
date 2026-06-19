"""Arize Phoenix OpenTelemetry integration."""

from __future__ import annotations

import os

_phoenix_enabled = False


def init_phoenix() -> bool:
    """Configure OTLP export to Phoenix."""
    global _phoenix_enabled

    from app.platform.config_loader import get_platform_config
    cfg = get_platform_config()._load("observability.yaml")
    if not cfg.get("phoenix", {}).get("enabled", True):
        return False

    endpoint = os.getenv("PHOENIX_OTLP_ENDPOINT") or cfg.get("phoenix", {}).get(
        "otlp_endpoint", "http://localhost:4317"
    )

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        service_name = cfg.get("opentelemetry", {}).get("service_name", "enterprise-rag")
        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        _phoenix_enabled = True
        return True
    except Exception:
        _phoenix_enabled = False
        return False


def is_phoenix_enabled() -> bool:
    return _phoenix_enabled


def get_phoenix_ui_url() -> str:
    from app.platform.config_loader import get_platform_config
    cfg = get_platform_config()._load("observability.yaml")
    return os.getenv("PHOENIX_UI_URL") or cfg.get("phoenix", {}).get("ui_url", "http://localhost:6006")


def is_phoenix_server_running() -> bool:
    """Check if Phoenix UI is actually reachable (not just exporter configured)."""
    import httpx

    url = get_phoenix_ui_url()
    try:
        with httpx.Client(timeout=2.0) as client:
            resp = client.get(url)
            return resp.status_code < 500
    except Exception:
        return False
