"""Document chunking with recursive strategy."""

import hashlib
import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings
from app.models.schemas import DocumentChunk, DocumentMetadata


def create_chunker() -> RecursiveCharacterTextSplitter:
    settings = get_settings()
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def chunk_text(text: str, metadata: DocumentMetadata) -> list[DocumentChunk]:
    """Split text into chunks with metadata attached."""
    splitter = create_chunker()
    chunks = splitter.split_text(text)
    result = []
    for i, chunk_text_val in enumerate(chunks):
        chunk_id = hashlib.md5(f"{metadata.document_id}_{i}".encode()).hexdigest()[:16]
        result.append(
            DocumentChunk(
                chunk_id=chunk_id,
                text=chunk_text_val,
                metadata=DocumentMetadata(
                    document_id=metadata.document_id,
                    source=metadata.source,
                    department=metadata.department,
                    classification=metadata.classification,
                    allowed_roles=metadata.allowed_roles,
                    security_level=metadata.security_level,
                    page=metadata.page,
                    data_source=metadata.data_source,
                    extra={**metadata.extra, "chunk_index": i},
                ),
            )
        )
    return result
