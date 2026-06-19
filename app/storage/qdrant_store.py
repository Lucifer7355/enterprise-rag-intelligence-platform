"""Qdrant vector store with RBAC pre-filtering."""

import uuid
from typing import Any

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchAny,
    PointStruct,
    VectorParams,
)

from app.config import get_settings
from app.models.schemas import DocumentChunk
from app.security.rbac import get_effective_roles
from app.storage.embeddings import embed_texts


class QdrantStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.settings = get_settings()
        self._use_memory = True
        try:
            self.client = QdrantClient(host=self.settings.qdrant_host, port=self.settings.qdrant_port, timeout=3)
            self.client.get_collections()
            self._use_memory = False
        except Exception:
            self.client = QdrantClient(":memory:")
        self.collection = self.settings.qdrant_collection
        self._ensure_collection()
        self._initialized = True

    def _ensure_collection(self) -> None:
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection not in collections:
            dim = len(embed_texts(["test"])[0])
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )

    def reset_collection(self) -> None:
        try:
            self.client.delete_collection(self.collection)
        except Exception:
            pass
        self._ensure_collection()

    def _build_filter(self, role: str) -> Filter:
        roles = list(get_effective_roles(role))
        return Filter(
            must=[
                FieldCondition(key="allowed_roles", match=MatchAny(any=roles)),
            ]
        )

    def index_chunks(self, chunks: list[DocumentChunk]) -> None:
        if not chunks:
            return
        texts = [c.text for c in chunks]
        vectors = embed_texts(texts)
        points = []
        for chunk, vector in zip(chunks, vectors):
            points.append(
                PointStruct(
                    id=str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.chunk_id)),
                    vector=vector.tolist(),
                    payload={
                        "chunk_id": chunk.chunk_id,
                        "document_id": chunk.metadata.document_id,
                        "text": chunk.text,
                        "source": chunk.metadata.source,
                        "department": chunk.metadata.department,
                        "allowed_roles": chunk.metadata.allowed_roles,
                        "data_source": chunk.metadata.data_source,
                    },
                )
            )
        self.client.upsert(collection_name=self.collection, points=points)

    def search(self, query: str, role: str, top_k: int = 20) -> list[dict[str, Any]]:
        query_vector = embed_texts([query])[0].tolist()
        rbac_filter = self._build_filter(role)
        response = self.client.query_points(
            collection_name=self.collection,
            query=query_vector,
            query_filter=rbac_filter,
            limit=top_k,
            with_payload=True,
        )
        return [
            {
                "chunk_id": r.payload["chunk_id"],
                "score": r.score,
                "text": r.payload.get("text", ""),
                "source": r.payload.get("source", ""),
                "document_id": r.payload.get("document_id", ""),
            }
            for r in response.points
        ]
