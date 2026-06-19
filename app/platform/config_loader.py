"""YAML-driven platform configuration loader with hot-reload."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


class PlatformConfig:
    """Central config store — all behavior driven from YAML."""

    def __init__(self, config_dir: Path | None = None):
        self.config_dir = config_dir or CONFIG_DIR
        self.reload()

    def reload(self) -> None:
        self.platform = self._load("platform.yaml")
        self.rbac = self._load("rbac.yaml")
        self.routing = self._load("routing.yaml")
        self.connectors = self._load("connectors.yaml")
        self.sensitive_data = self._load("sensitive_data.yaml")
        self.graph = self._load("graph.yaml")
        self._compile_sensitive_patterns()

    def _load(self, filename: str) -> dict[str, Any]:
        path = self.config_dir / filename
        if not path.exists():
            return {}
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _compile_sensitive_patterns(self) -> None:
        self._sensitive_compiled: list[dict] = []
        for name, cfg in self.sensitive_data.get("patterns", {}).items():
            self._sensitive_compiled.append({
                "name": name,
                "regex": re.compile(cfg["regex"]),
                "action": cfg.get("action", "block"),
                "allowed_roles": set(cfg.get("allowed_roles", [])),
                "denial_message": cfg.get("denial_message", "Access Denied: Insufficient permissions."),
                "redact_with": cfg.get("redact_with", "[REDACTED]"),
            })

    @property
    def sensitive_patterns(self) -> list[dict]:
        return self._sensitive_compiled

    def get_role_hierarchy(self) -> dict[str, set[str]]:
        """Build effective role access map from rbac.yaml."""
        roles_cfg = self.rbac.get("roles", {})
        hierarchy: dict[str, set[str]] = {}

        def resolve(role: str, visited: set[str] | None = None) -> set[str]:
            if role in hierarchy:
                return hierarchy[role]
            visited = visited or set()
            if role in visited:
                return {role}
            visited.add(role)
            effective = {role}
            cfg = roles_cfg.get(role, {})
            for inherited in cfg.get("inherits", []):
                effective.update(resolve(inherited, visited))
            hierarchy[role] = effective
            return effective

        for role_name in roles_cfg:
            resolve(role_name)
        return hierarchy

    def get_effective_roles(self, role: str) -> set[str]:
        hierarchy = self.get_role_hierarchy()
        return hierarchy.get(role, {role})

    def list_roles(self) -> list[str]:
        return list(self.rbac.get("roles", {}).keys())

    def validate_role(self, role: str) -> str:
        roles = self.list_roles()
        if role not in roles:
            default = self.rbac.get("default_role", roles[0] if roles else "Engineering")
            return default
        return role

    def get_query_types(self) -> list[dict]:
        return self.routing.get("query_types", [])

    def get_connectors(self) -> list[dict]:
        return [c for c in self.connectors.get("connectors", []) if c.get("enabled", True)]

    def get_connector_by_name(self, name: str) -> dict | None:
        for c in self.connectors.get("connectors", []):
            if c.get("name") == name:
                return c
        return None

    def add_connector(self, connector: dict) -> None:
        connectors = self.connectors.setdefault("connectors", [])
        connectors = [c for c in connectors if c.get("name") != connector.get("name")]
        connectors.append(connector)
        self.connectors["connectors"] = connectors
        self._persist_connectors()

    def remove_connector(self, name: str) -> bool:
        connectors = self.connectors.get("connectors", [])
        new_list = [c for c in connectors if c.get("name") != name]
        if len(new_list) == len(connectors):
            return False
        self.connectors["connectors"] = new_list
        self._persist_connectors()
        return True

    def _persist_connectors(self) -> None:
        path = self.config_dir / "connectors.yaml"
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(self.connectors, f, default_flow_style=False, sort_keys=False)

    def get_auto_tag_patterns(self) -> list[dict]:
        patterns = self.connectors.get("auto_tag_patterns", [])
        compiled = []
        for p in patterns:
            compiled.append({
                "regex": re.compile(p["pattern"]),
                "metadata": p.get("metadata", {}),
            })
        return compiled

    def get_retrieval_settings(self) -> dict:
        return self.platform.get("retrieval", {})


@lru_cache
def get_platform_config() -> PlatformConfig:
    return PlatformConfig()


def reload_platform_config() -> PlatformConfig:
    get_platform_config.cache_clear()
    cfg = get_platform_config()
    cfg.reload()
    return cfg
