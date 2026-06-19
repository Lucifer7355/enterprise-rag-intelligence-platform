"""Pydantic schemas for API and internal models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.platform.config_loader import get_platform_config


class DocumentMetadata(BaseModel):
    document_id: str
    source: str
    department: str
    classification: str = "internal"
    allowed_roles: list[str]
    security_level: str = "internal"
    page: int | None = None
    data_source: str = "unknown"
    extra: dict[str, Any] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    chunk_id: str
    text: str
    metadata: DocumentMetadata


class ChatRequest(BaseModel):
    query: str
    user_id: str = "user001"
    role: str = "Engineering"

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        return get_platform_config().validate_role(v)


class SourceCitation(BaseModel):
    document_id: str
    source: str
    page: int | None = None
    confidence: float
    snippet: str = ""


class RetrievalTrace(BaseModel):
    query_type: str
    routed_sources: list[str]
    retrieved_documents: list[str]
    authorized_doc_count: int
    blocked_sensitive: bool = False


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceCitation]
    retrieval_trace: RetrievalTrace
    latency_ms: float


class IngestRequest(BaseModel):
    regenerate_synthetic: bool = False
    force_reindex: bool = False


class IngestResponse(BaseModel):
    status: str
    documents_ingested: int
    chunks_created: int
    message: str


class SourceInfo(BaseModel):
    document_id: str
    source: str
    department: str
    classification: str
    allowed_roles: list[str]
    data_source: str


class AuditEntry(BaseModel):
    timestamp: datetime
    user_id: str
    role: str
    action: str
    query: str | None = None
    result: str
    details: dict[str, Any] = Field(default_factory=dict)


class EvaluateRequest(BaseModel):
    test_queries: list[dict[str, Any]] | None = None


class EvaluateResponse(BaseModel):
    retrieval_metrics: dict[str, float]
    generation_metrics: dict[str, float]
    security_metrics: dict[str, int]
    evaluation_method: str = "heuristic_live"


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    role: str
    auth_method: str = "local"


class ConnectorConfig(BaseModel):
    name: str
    type: str
    enabled: bool = True
    path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    file_patterns: list[str] | None = None
    tables: dict[str, Any] | None = None
    pattern_rules: list[dict[str, Any]] | None = None
    items: list[dict[str, Any]] | None = None


class InlineDocumentRequest(BaseModel):
    connector_name: str = "runtime_docs"
    document_id: str
    source: str
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConfigReloadResponse(BaseModel):
    status: str
    roles: list[str]
    connectors: list[str]
    query_types: list[str]
