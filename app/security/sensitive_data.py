"""Config-driven sensitive data detection and handling."""

from __future__ import annotations

from app.platform.config_loader import get_platform_config


def detect_sensitive_content(text: str) -> list[str]:
    cfg = get_platform_config()
    found = []
    for pattern in cfg.sensitive_patterns:
        if pattern["regex"].search(text):
            found.append(pattern["name"])
    return found


def process_sensitive_text(text: str, role: str) -> tuple[str | None, str | None, str]:
    """
    Process text for sensitive content based on config.
    Returns (processed_text, denial_message, action_taken).
    action_taken: allowed | blocked | redacted | skipped
    """
    cfg = get_platform_config()

    for pattern in cfg.sensitive_patterns:
        if not pattern["regex"].search(text):
            continue

        if role in pattern["allowed_roles"]:
            if pattern["action"] == "redact":
                text = pattern["regex"].sub(pattern["redact_with"], text)
                return text, None, "redacted"
            return text, None, "allowed"

        if pattern["action"] == "skip_chunk":
            return None, None, "skipped"

        if pattern["action"] == "redact":
            text = pattern["regex"].sub(pattern["redact_with"], text)
            return text, None, "redacted"

        return None, pattern["denial_message"], "blocked"

    return text, None, "allowed"


def check_sensitive_access(text: str, role: str) -> tuple[bool, str | None]:
    """Backward-compatible block check — used when action is 'block'."""
    processed, denial, action = process_sensitive_text(text, role)
    if action == "blocked":
        return False, denial
    if action == "skipped":
        return False, None  # signal to skip chunk, not deny entire query
    return True, None
