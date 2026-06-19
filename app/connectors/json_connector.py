"""JSON connector — reads JSON log files from a directory."""

from __future__ import annotations

import fnmatch
import json
from pathlib import Path

from app.connectors.base import BaseConnector
from app.ingestion.metadata_tagger import MetadataTagger
from app.models.schemas import DocumentMetadata


class JsonConnector(BaseConnector):
    connector_type = "json"

    def fetch(self) -> list[tuple[str, DocumentMetadata]]:
        base_path = Path(self.config.get("path", "."))
        if not base_path.exists():
            return []

        tagger = MetadataTagger()
        defaults = self.default_metadata()
        pattern_rules = self.config.get("pattern_rules", [])
        documents = []

        for json_file in base_path.glob("*.json"):
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)

            entries = data if isinstance(data, list) else [data]
            file_meta = self._match_pattern_rules(json_file.name, pattern_rules, defaults)

            for i, entry in enumerate(entries):
                doc_id = f"{json_file.stem}_{i}"
                text = json.dumps(entry, indent=2)
                meta_data = tagger.auto_tag(json_file.name, file_meta)
                documents.append((
                    text,
                    DocumentMetadata(
                        document_id=doc_id,
                        source=json_file.name,
                        department=meta_data.get("department", "general"),
                        classification=meta_data.get("classification", "internal"),
                        allowed_roles=meta_data.get("allowed_roles", ["Admin"]),
                        data_source=meta_data.get("data_source", "json_log"),
                        extra={"connector": self.name},
                    ),
                ))
        return documents

    def _match_pattern_rules(
        self, filename: str, rules: list[dict], defaults: dict
    ) -> dict:
        result = dict(defaults)
        for rule in rules:
            if fnmatch.fnmatch(filename, rule.get("pattern", "*")):
                result.update(rule.get("metadata", {}))
        return result
