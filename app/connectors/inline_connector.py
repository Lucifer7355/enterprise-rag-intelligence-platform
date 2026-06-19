"""Inline connector — documents submitted via API at runtime."""

from __future__ import annotations

from app.connectors.base import BaseConnector
from app.ingestion.metadata_tagger import MetadataTagger
from app.models.schemas import DocumentMetadata

_INLINE_STORE: dict[str, list[tuple[str, DocumentMetadata]]] = {}


class InlineConnector(BaseConnector):
    connector_type = "inline"

    def fetch(self) -> list[tuple[str, DocumentMetadata]]:
        return _INLINE_STORE.get(self.name, [])

    @staticmethod
    def add_document(
        connector_name: str,
        text: str,
        document_id: str,
        source: str,
        metadata: dict,
    ) -> None:
        tagger = MetadataTagger()
        meta_data = tagger.auto_tag(source, metadata)
        doc = (
            text,
            DocumentMetadata(
                document_id=document_id,
                source=source,
                department=meta_data.get("department", "general"),
                classification=meta_data.get("classification", "internal"),
                allowed_roles=meta_data.get("allowed_roles", ["Admin"]),
                data_source=meta_data.get("data_source", "inline"),
                extra={"connector": connector_name},
            ),
        )
        _INLINE_STORE.setdefault(connector_name, []).append(doc)

    @staticmethod
    def clear(connector_name: str) -> None:
        _INLINE_STORE.pop(connector_name, None)
