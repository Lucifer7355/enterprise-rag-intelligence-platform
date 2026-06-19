"""Connector-driven ingestion pipeline — no hardcoded data sources."""

from pathlib import Path

from app.config import get_settings
from app.connectors.registry import create_connector, initialize_registry
from app.connectors.sql_connector import SqlConnector
from app.ingestion.chunker import chunk_text
from app.knowledge_graph.graph import KnowledgeGraph
from app.models.schemas import DocumentChunk
from app.observability.logging import get_logger
from app.platform.config_loader import get_platform_config
from app.storage.document_store import DocumentStore
from app.storage.elasticsearch_store import ElasticsearchStore
from app.storage.qdrant_store import QdrantStore

logger = get_logger(__name__)


class IngestionPipeline:
    def __init__(self):
        self.settings = get_settings()
        self.doc_store = DocumentStore()
        self.qdrant = QdrantStore()
        self.es = ElasticsearchStore()
        self.kg = KnowledgeGraph()
        initialize_registry()

    def load_all_documents(self) -> tuple[list[DocumentChunk], Path | None]:
        cfg = get_platform_config()
        all_chunks: list[DocumentChunk] = []
        sql_db_path: Path | None = None

        for connector_cfg in cfg.get_connectors():
            connector = create_connector(connector_cfg)
            if connector is None or not connector.is_enabled():
                continue

            logger.info("connector_fetching", name=connector.name, type=connector_cfg.get("type"))
            try:
                documents = connector.fetch()
            except Exception as e:
                logger.warning("connector_failed", name=connector.name, error=str(e))
                continue

            for text, meta in documents:
                all_chunks.extend(chunk_text(text, meta))

            if isinstance(connector, SqlConnector):
                sql_db_path = connector.get_db_path()

        return all_chunks, sql_db_path

    def run(self, force_reindex: bool = False) -> dict:
        logger.info("ingestion_started", force_reindex=force_reindex)

        if force_reindex:
            self.qdrant.reset_collection()
            self.es.reset_index()

        chunks, sql_db_path = self.load_all_documents()

        if not chunks:
            return {
                "status": "error",
                "documents_ingested": 0,
                "chunks_created": 0,
                "message": "No data found. Add connectors in config/connectors.yaml and retry.",
            }

        self.doc_store.index_chunks(chunks)
        self.qdrant.index_chunks(chunks)
        self.es.index_chunks(chunks)

        if sql_db_path:
            import networkx as nx
            self.kg.graph = nx.DiGraph()
            self.kg._loaded = True
            self.kg.build_from_sql(sql_db_path)
            self.kg.save()

        doc_count = len({c.metadata.document_id for c in chunks})
        connector_count = len(get_platform_config().get_connectors())
        logger.info("ingestion_complete", documents=doc_count, chunks=len(chunks))

        return {
            "status": "success",
            "documents_ingested": doc_count,
            "chunks_created": len(chunks),
            "message": f"Ingested {doc_count} documents from {connector_count} connectors into {len(chunks)} chunks",
        }
