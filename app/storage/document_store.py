"""In-memory document metadata and chunk registry."""

from app.models.schemas import DocumentChunk, DocumentMetadata, SourceInfo


class DocumentStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._chunks: dict[str, DocumentChunk] = {}
            cls._instance._doc_metadata: dict[str, DocumentMetadata] = {}
        return cls._instance

    def index_chunks(self, chunks: list[DocumentChunk]) -> None:
        for chunk in chunks:
            self._chunks[chunk.chunk_id] = chunk
            self._doc_metadata[chunk.metadata.document_id] = chunk.metadata

    def get_chunk(self, chunk_id: str) -> DocumentChunk | None:
        return self._chunks.get(chunk_id)

    def get_chunks_by_ids(self, chunk_ids: list[str]) -> list[DocumentChunk]:
        return [self._chunks[cid] for cid in chunk_ids if cid in self._chunks]

    def get_all_metadata(self) -> dict[str, DocumentMetadata]:
        return self._doc_metadata.copy()

    def list_sources(self) -> list[SourceInfo]:
        seen = set()
        sources = []
        for doc_id, meta in self._doc_metadata.items():
            if doc_id not in seen:
                seen.add(doc_id)
                sources.append(
                    SourceInfo(
                        document_id=doc_id,
                        source=meta.source,
                        department=meta.department,
                        classification=meta.classification,
                        allowed_roles=meta.allowed_roles,
                        data_source=meta.data_source,
                    )
                )
        return sources

    def get_chunks_for_docs(self, doc_ids: set[str]) -> list[DocumentChunk]:
        return [c for c in self._chunks.values() if c.metadata.document_id in doc_ids]
