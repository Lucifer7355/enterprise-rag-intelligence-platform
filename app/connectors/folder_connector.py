"""Folder connector — reads text/PDF files from any directory."""

from __future__ import annotations

import fnmatch
import json
from pathlib import Path

from app.connectors.base import BaseConnector
from app.ingestion.metadata_tagger import MetadataTagger
from app.models.schemas import DocumentMetadata


class FolderConnector(BaseConnector):
    connector_type = "folder"

    def fetch(self) -> list[tuple[str, DocumentMetadata]]:
        base_path = Path(self.config.get("path", "."))
        if not base_path.exists():
            return []

        patterns = self.config.get("file_patterns", ["*.txt", "*.pdf"])
        tagger = MetadataTagger()
        documents = []

        for pattern in patterns:
            for file_path in base_path.glob(pattern):
                if not file_path.is_file():
                    continue

                if file_path.suffix.lower() == ".pdf":
                    text = self._read_pdf(file_path)
                else:
                    text = file_path.read_text(encoding="utf-8", errors="ignore")

                if not text.strip():
                    continue

                meta = self._resolve_metadata(file_path, tagger)
                documents.append((text, meta))

        return documents

    def _read_pdf(self, path: Path) -> str:
        try:
            import fitz
            doc = fitz.open(path)
            return "\n".join(page.get_text() for page in doc)
        except Exception:
            txt = path.with_suffix(".txt")
            if txt.exists():
                return txt.read_text(encoding="utf-8", errors="ignore")
            return ""

    def _resolve_metadata(self, file_path: Path, tagger: MetadataTagger) -> DocumentMetadata:
        meta_file = file_path.with_name(file_path.stem + "_meta.json")
        if meta_file.exists():
            meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
        else:
            meta_data = tagger.auto_tag(str(file_path), self.default_metadata())

        source_name = file_path.name if file_path.suffix == ".pdf" else file_path.stem + ".pdf"
        doc_id = file_path.stem.replace(" ", "_").lower()

        return DocumentMetadata(
            document_id=doc_id,
            source=source_name,
            department=meta_data.get("department", "general"),
            classification=meta_data.get("classification", "internal"),
            allowed_roles=meta_data.get("allowed_roles", ["Admin"]),
            security_level=meta_data.get("classification", "internal"),
            data_source=meta_data.get("data_source", "pdf"),
            extra={"connector": self.name},
        )
