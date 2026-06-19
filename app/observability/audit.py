"""Audit log persistence."""

import json
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings
from app.models.schemas import AuditEntry


class AuditLogger:
    def __init__(self):
        self.settings = get_settings()
        self.path = Path(self.settings.audit_log_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: list[AuditEntry] = []

    def log(
        self,
        user_id: str,
        role: str,
        action: str,
        result: str,
        query: str | None = None,
        details: dict | None = None,
    ) -> AuditEntry:
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            role=role,
            action=action,
            query=query,
            result=result,
            details=details or {},
        )
        self._entries.append(entry)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(entry.model_dump_json() + "\n")
        return entry

    def get_entries(self, limit: int = 100) -> list[AuditEntry]:
        entries = []
        if self.path.exists():
            lines = self.path.read_text(encoding="utf-8").strip().split("\n")
            for line in lines[-limit:]:
                if line:
                    entries.append(AuditEntry.model_validate_json(line))
        return entries or self._entries[-limit:]

    def security_stats(self) -> dict[str, int]:
        entries = self.get_entries(limit=10000)
        return {
            "unauthorized_access_attempts": sum(
                1 for e in entries if e.result == "denied" and "rbac" in e.action
            ),
            "blocked_queries": sum(1 for e in entries if e.result == "blocked"),
            "permission_violations": sum(
                1 for e in entries if e.result == "denied" and "sensitive" in e.action
            ),
        }


audit_logger = AuditLogger()
