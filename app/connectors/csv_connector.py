"""CSV connector — reads all CSV files from a directory."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.connectors.base import BaseConnector
from app.ingestion.metadata_tagger import MetadataTagger
from app.models.schemas import DocumentMetadata


class CsvConnector(BaseConnector):
    connector_type = "csv"

    def fetch(self) -> list[tuple[str, DocumentMetadata]]:
        base_path = Path(self.config.get("path", "."))
        if not base_path.exists():
            return []

        tagger = MetadataTagger()
        defaults = self.default_metadata()
        documents = []

        for csv_file in base_path.glob("*.csv"):
            df = pd.read_csv(csv_file)
            for i, row in df.iterrows():
                doc_id = f"{csv_file.stem}_{i}"
                text = f"Record from {csv_file.name}\n" + "\n".join(
                    f"{col}: {row[col]}" for col in df.columns
                )
                meta_data = tagger.auto_tag(csv_file.name, defaults)
                documents.append((
                    text,
                    DocumentMetadata(
                        document_id=doc_id,
                        source=csv_file.name,
                        department=meta_data.get("department", "general"),
                        classification=meta_data.get("classification", "internal"),
                        allowed_roles=meta_data.get("allowed_roles", ["Admin"]),
                        data_source=meta_data.get("data_source", "csv"),
                        extra={"connector": self.name},
                    ),
                ))
        return documents
