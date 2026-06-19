"""Elasticsearch BM25 sparse retrieval with RBAC filtering."""

from typing import Any

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from app.config import get_settings
from app.models.schemas import DocumentChunk
from app.security.rbac import get_effective_roles


class ElasticsearchStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
            cls._instance._fallback_corpus: list[dict] = []
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.settings = get_settings()
        self.index = self.settings.elasticsearch_index
        self._connected = False
        try:
            self.client = Elasticsearch(self.settings.elasticsearch_url, request_timeout=3)
            self._connected = self.client.ping()
        except Exception:
            self._connected = False
        self._initialized = True

    def reset_index(self) -> None:
        if self._connected:
            if self.client.indices.exists(index=self.index):
                self.client.indices.delete(index=self.index)
            self._create_index()
        else:
            self._fallback_corpus = []

    def _create_index(self) -> None:
        if not self._connected:
            return
        self.client.indices.create(
            index=self.index,
            body={
                "mappings": {
                    "properties": {
                        "chunk_id": {"type": "keyword"},
                        "document_id": {"type": "keyword"},
                        "text": {"type": "text"},
                        "source": {"type": "keyword"},
                        "allowed_roles": {"type": "keyword"},
                        "department": {"type": "keyword"},
                        "data_source": {"type": "keyword"},
                    }
                }
            },
            ignore=400,
        )

    def index_chunks(self, chunks: list[DocumentChunk]) -> None:
        if self._connected:
            self._create_index()
            actions = [
                {
                    "_index": self.index,
                    "_id": chunk.chunk_id,
                    "_source": {
                        "chunk_id": chunk.chunk_id,
                        "document_id": chunk.metadata.document_id,
                        "text": chunk.text,
                        "source": chunk.metadata.source,
                        "allowed_roles": chunk.metadata.allowed_roles,
                        "department": chunk.metadata.department,
                        "data_source": chunk.metadata.data_source,
                    },
                }
                for chunk in chunks
            ]
            bulk(self.client, actions, raise_on_error=False)
            self.client.indices.refresh(index=self.index)
        else:
            self._fallback_corpus = [
                {
                    "chunk_id": c.chunk_id,
                    "document_id": c.metadata.document_id,
                    "text": c.text,
                    "source": c.metadata.source,
                    "allowed_roles": c.metadata.allowed_roles,
                }
                for c in chunks
            ]

    def _fallback_bm25_search(self, query: str, role: str, top_k: int) -> list[dict[str, Any]]:
        from rank_bm25 import BM25Okapi

        roles = get_effective_roles(role)
        authorized = [d for d in self._fallback_corpus if roles.intersection(set(d["allowed_roles"]))]
        if not authorized:
            return []
        tokenized = [d["text"].lower().split() for d in authorized]
        bm25 = BM25Okapi(tokenized)
        scores = bm25.get_scores(query.lower().split())
        ranked = sorted(zip(authorized, scores), key=lambda x: x[1], reverse=True)[:top_k]
        max_score = ranked[0][1] if ranked and ranked[0][1] > 0 else 1.0
        return [
            {
                "chunk_id": doc["chunk_id"],
                "score": score / max_score,
                "text": doc["text"],
                "source": doc["source"],
                "document_id": doc["document_id"],
            }
            for doc, score in ranked
            if score > 0
        ]

    def search(self, query: str, role: str, top_k: int = 20) -> list[dict[str, Any]]:
        roles = list(get_effective_roles(role))
        if not self._connected:
            return self._fallback_bm25_search(query, role, top_k)

        body = {
            "query": {
                "bool": {
                    "must": [{"match": {"text": query}}],
                    "filter": [{"terms": {"allowed_roles": roles}}],
                }
            },
            "size": top_k,
        }
        try:
            resp = self.client.search(index=self.index, body=body)
            hits = resp["hits"]["hits"]
            max_score = resp["hits"]["max_score"] or 1.0
            return [
                {
                    "chunk_id": h["_source"]["chunk_id"],
                    "score": (h["_score"] or 0) / max_score,
                    "text": h["_source"]["text"],
                    "source": h["_source"]["source"],
                    "document_id": h["_source"]["document_id"],
                }
                for h in hits
            ]
        except Exception:
            return self._fallback_bm25_search(query, role, top_k)
