"""PDF connector — alias for folder connector focused on PDF directories."""

from app.connectors.folder_connector import FolderConnector


class PdfConnector(FolderConnector):
    connector_type = "pdf"

    def fetch(self):
        if "file_patterns" not in self.config:
            self.config["file_patterns"] = ["*.pdf", "*.txt"]
        return super().fetch()
