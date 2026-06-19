"""Langfuse LLM observability integration."""

from __future__ import annotations

import os
from typing import Any

from app.platform.config_loader import get_platform_config

_langfuse = None
_local_traces: list[dict] = []
_enabled = False


def init_langfuse() -> bool:
    global _langfuse, _enabled
    cfg = get_platform_config()._load("observability.yaml")
    if not cfg.get("langfuse", {}).get("enabled", True):
        return False

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
    host = os.getenv("LANGFUSE_HOST") or cfg.get("langfuse", {}).get("host", "http://localhost:3000")

    if not public_key or not secret_key:
        _enabled = False
        return False

    try:
        from langfuse import Langfuse
        _langfuse = Langfuse(public_key=public_key, secret_key=secret_key, host=host)
        _enabled = True
        return True
    except Exception:
        _enabled = False
        return False


def is_enabled() -> bool:
    return _enabled and _langfuse is not None


def start_trace(name: str, user_id: str | None = None, metadata: dict | None = None) -> Any:
    entry = {"name": name, "user_id": user_id, "metadata": metadata or {}, "spans": []}
    _local_traces.append(entry)

    if is_enabled():
        try:
            return _langfuse.trace(name=name, user_id=user_id, metadata=metadata)
        except Exception:
            pass
    return entry


def start_span(trace: Any, name: str, metadata: dict | None = None) -> Any:
    if is_enabled() and hasattr(trace, "span"):
        try:
            return trace.span(name=name, metadata=metadata)
        except Exception:
            pass
    if isinstance(trace, dict):
        span = {"name": name, "metadata": metadata or {}}
        trace["spans"].append(span)
        return span
    return None


def end_span(span: Any, output: Any = None) -> None:
    if span is None:
        return
    if is_enabled() and hasattr(span, "end"):
        try:
            span.end(output=output)
            return
        except Exception:
            pass
    if isinstance(span, dict):
        span["output"] = output


def log_generation(trace: Any, name: str, input_text: str, output_text: str, metadata: dict | None = None) -> None:
    if is_enabled() and hasattr(trace, "generation"):
        try:
            trace.generation(name=name, input=input_text, output=output_text, metadata=metadata)
            return
        except Exception:
            pass


def flush() -> None:
    if is_enabled():
        try:
            _langfuse.flush()
        except Exception:
            pass


def get_local_traces(limit: int = 50) -> list[dict]:
    return _local_traces[-limit:]
