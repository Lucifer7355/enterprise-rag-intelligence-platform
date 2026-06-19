"""Auto-metadata tagging from config rules."""

from __future__ import annotations

from app.platform.config_loader import get_platform_config


class MetadataTagger:
    def auto_tag(self, identifier: str, defaults: dict | None = None) -> dict:
        """Apply auto-tag patterns from connectors.yaml to an identifier (filename/path)."""
        cfg = get_platform_config()
        result = dict(defaults or {})
        if not cfg.platform.get("metadata", {}).get("use_pattern_rules", True):
            return result

        for pattern in cfg.get_auto_tag_patterns():
            if pattern["regex"].search(identifier):
                result.update(pattern["metadata"])
        return result
