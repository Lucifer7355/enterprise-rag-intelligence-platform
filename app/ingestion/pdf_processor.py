"""PDF and text document processing."""

import json
from pathlib import Path

from app.models.schemas import DocumentMetadata


def process_text_documents(pdf_dir: Path) -> list[tuple[str, DocumentMetadata]]:
    """Process text files (PDF content stored as .txt for synthetic data)."""
    documents = []
    for txt_file in pdf_dir.glob("*.txt"):
        meta_file = pdf_dir / txt_file.name.replace(".txt", "_meta.json")
        if meta_file.exists():
            meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
        else:
            meta_data = {
                "department": "general",
                "classification": "internal",
                "allowed_roles": ["Admin"],
                "data_source": "pdf",
            }

        text = txt_file.read_text(encoding="utf-8")
        source_name = txt_file.name.replace(".txt", ".pdf")
        doc_id = source_name.replace(".pdf", "").replace(" ", "_").lower()

        meta = DocumentMetadata(
            document_id=doc_id,
            source=source_name,
            department=meta_data["department"],
            classification=meta_data["classification"],
            allowed_roles=meta_data["allowed_roles"],
            security_level=meta_data.get("classification", "internal"),
            page=1,
            data_source=meta_data.get("data_source", "pdf"),
        )
        documents.append((text, meta))
    return documents
