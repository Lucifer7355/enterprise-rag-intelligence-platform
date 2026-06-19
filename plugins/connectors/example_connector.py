"""
Example custom connector plugin.

To add your own data source:
  1. Copy this file to plugins/connectors/my_connector.py
  2. Implement fetch() returning list of (text, DocumentMetadata)
  3. Add an entry in config/connectors.yaml with type: my_type
  4. POST /ingest

No changes to core application code required.
"""

from app.connectors.base import BaseConnector
from app.models.schemas import DocumentMetadata


class ExampleConnector(BaseConnector):
    connector_type = "example"

    def fetch(self) -> list[tuple[str, DocumentMetadata]]:
        # Replace with your data source logic (API, DB, S3, etc.)
        items = self.config.get("items", [])
        documents = []
        defaults = self.default_metadata()

        for i, item in enumerate(items):
            documents.append((
                item.get("text", ""),
                DocumentMetadata(
                    document_id=item.get("id", f"example_{i}"),
                    source=item.get("source", "example"),
                    department=defaults.get("department", "general"),
                    classification=defaults.get("classification", "internal"),
                    allowed_roles=defaults.get("allowed_roles", ["Admin"]),
                    data_source=defaults.get("data_source", "example"),
                    extra={"connector": self.name},
                ),
            ))
        return documents
