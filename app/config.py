"""Application configuration."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "BAAI/bge-large-en-v1.5"
    reranker_model: str = "BAAI/bge-reranker-base"

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "enterprise_docs"

    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_index: str = "enterprise_docs"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    use_mock_llm: bool = False

    chunk_size: int = 500
    chunk_overlap: int = 100
    hybrid_semantic_weight: float = 0.6
    hybrid_bm25_weight: float = 0.4
    top_k_retrieval: int = 20
    top_k_rerank: int = 5

    data_dir: str = "data/synthetic"
    graph_path: str = "data/knowledge_graph.json"
    audit_log_path: str = "data/audit_log.jsonl"


@lru_cache
def get_settings() -> Settings:
    return Settings()
