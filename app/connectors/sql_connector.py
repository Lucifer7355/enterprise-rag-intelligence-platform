"""SQL connector — reads SQLite tables with configurable templates."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from app.connectors.base import BaseConnector
from app.models.schemas import DocumentMetadata


class SqlConnector(BaseConnector):
    connector_type = "sql"

    def fetch(self) -> list[tuple[str, DocumentMetadata]]:
        db_path = Path(self.config.get("path", ""))
        if not db_path.exists():
            return []

        tables_cfg = self.config.get("tables", {})
        documents = []
        conn = sqlite3.connect(db_path)

        for table_name, table_cfg in tables_cfg.items():
            try:
                df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
            except Exception:
                continue

            template = table_cfg.get("template", "{row}")
            id_field = table_cfg.get("id_field", df.columns[0] if len(df.columns) else "id")
            meta_defaults = table_cfg.get("metadata", self.default_metadata())

            for _, row in df.iterrows():
                row_dict = row.to_dict()
                text = template.format(**row_dict)
                doc_id = f"{table_name}_{row_dict.get(id_field, row.name)}"

                documents.append((
                    text,
                    DocumentMetadata(
                        document_id=str(doc_id).replace(" ", "_").lower(),
                        source=f"{table_name}.sql",
                        department=meta_defaults.get("department", "general"),
                        classification=meta_defaults.get("classification", "internal"),
                        allowed_roles=meta_defaults.get("allowed_roles", ["Admin"]),
                        data_source=meta_defaults.get("data_source", "sql"),
                        extra={"connector": self.name, "table": table_name},
                    ),
                ))

        conn.close()
        return documents

    def get_db_path(self) -> Path | None:
        path = Path(self.config.get("path", ""))
        return path if path.exists() else None
