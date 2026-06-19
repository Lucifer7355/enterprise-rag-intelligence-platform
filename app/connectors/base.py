"""Base connector interface — implement this to add custom data sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.models.schemas import DocumentMetadata


class BaseConnector(ABC):
    """Plugin interface for data source connectors."""

    connector_type: str = "base"

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.name = config.get("name", "unnamed")

    @abstractmethod
    def fetch(self) -> list[tuple[str, DocumentMetadata]]:
        """
        Fetch documents from the data source.
        Returns list of (text_content, metadata) tuples.
        """
        ...

    def is_enabled(self) -> bool:
        return self.config.get("enabled", True)

    def default_metadata(self) -> dict[str, Any]:
        return self.config.get("metadata", {})
