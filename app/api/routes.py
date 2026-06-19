"""FastAPI route handlers — plug-and-play management APIs."""

from fastapi import APIRouter, Depends, HTTPException

from app.security.auth import get_current_user, is_auth_required

from app.connectors.inline_connector import InlineConnector
from app.connectors.registry import initialize_registry, list_connector_types
from app.evaluation.metrics import EvaluationFramework
from app.ingestion.pipeline import IngestionPipeline
from app.models.schemas import (
    AuditEntry,
    ChatRequest,
    ChatResponse,
    ConfigReloadResponse,
    ConnectorConfig,
    EvaluateRequest,
    EvaluateResponse,
    InlineDocumentRequest,
    IngestRequest,
    IngestResponse,
    SourceInfo,
)
from app.observability.audit import audit_logger
from app.platform.config_loader import get_platform_config, reload_platform_config
from app.retrieval.pipeline import RetrievalPipeline
from app.storage.document_store import DocumentStore

router = APIRouter()
retrieval_pipeline = RetrievalPipeline()
ingestion_pipeline = IngestionPipeline()
doc_store = DocumentStore()
evaluator = EvaluationFramework()

initialize_registry()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict | None = Depends(get_current_user),
) -> ChatResponse:
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    if is_auth_required() and not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    user_id = current_user["user_id"] if current_user else request.user_id
    role = current_user["role"] if current_user else request.role
    return retrieval_pipeline.process(request.query, user_id, role)


@router.post("/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest) -> IngestResponse:
    cfg = get_platform_config()
    if request.regenerate_synthetic and cfg.platform.get("platform", {}).get("sample_data_enabled", True):
        from scripts.generate_synthetic_data import main as generate_data
        generate_data()

    result = ingestion_pipeline.run(force_reindex=request.force_reindex)
    return IngestResponse(**result)


@router.get("/sources", response_model=list[SourceInfo])
async def get_sources() -> list[SourceInfo]:
    return doc_store.list_sources()


@router.get("/audit", response_model=list[AuditEntry])
async def get_audit(limit: int = 100) -> list[AuditEntry]:
    return audit_logger.get_entries(limit=limit)


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate(request: EvaluateRequest) -> EvaluateResponse:
    return evaluator.run(request.test_queries)


@router.get("/roles")
async def get_roles() -> dict:
    cfg = get_platform_config()
    return {
        "roles": cfg.list_roles(),
        "default_role": cfg.rbac.get("default_role", "Engineering"),
        "hierarchy": {k: list(v) for k, v in cfg.get_role_hierarchy().items()},
    }


@router.get("/connectors")
async def get_connectors() -> dict:
    cfg = get_platform_config()
    return {
        "registered_types": list_connector_types(),
        "configured": [
            {"name": c.get("name"), "type": c.get("type"), "enabled": c.get("enabled", True), "path": c.get("path")}
            for c in cfg.get_connectors()
        ],
    }


@router.post("/connectors", response_model=dict)
async def add_connector(connector: ConnectorConfig) -> dict:
    cfg = get_platform_config()
    cfg.add_connector(connector.model_dump(exclude_none=True))
    reload_platform_config()
    return {"status": "added", "name": connector.name}


@router.delete("/connectors/{name}")
async def remove_connector(name: str) -> dict:
    cfg = get_platform_config()
    if not cfg.remove_connector(name):
        raise HTTPException(status_code=404, detail=f"Connector '{name}' not found")
    reload_platform_config()
    return {"status": "removed", "name": name}


@router.post("/documents", response_model=dict)
async def add_inline_document(request: InlineDocumentRequest) -> dict:
    """Add a document at runtime without editing config files."""
    cfg = get_platform_config()
    connector_cfg = cfg.get_connector_by_name(request.connector_name)
    if connector_cfg is None:
        cfg.add_connector({
            "name": request.connector_name,
            "type": "inline",
            "enabled": True,
            "metadata": request.metadata,
        })
        reload_platform_config()

    InlineConnector.add_document(
        request.connector_name,
        request.text,
        request.document_id,
        request.source,
        request.metadata,
    )
    result = ingestion_pipeline.run(force_reindex=False)
    return {**result, "status": "indexed", "document_id": request.document_id}


@router.post("/config/reload", response_model=ConfigReloadResponse)
async def reload_config() -> ConfigReloadResponse:
    cfg = reload_platform_config()
    return ConfigReloadResponse(
        status="reloaded",
        roles=cfg.list_roles(),
        connectors=[c.get("name", "") for c in cfg.get_connectors()],
        query_types=[qt["name"] for qt in cfg.get_query_types()],
    )


@router.get("/observability")
async def get_observability_status() -> dict:
    from app.observability.langfuse_client import is_enabled as langfuse_on, get_local_traces
    from app.observability.phoenix_setup import (
        get_phoenix_ui_url,
        is_phoenix_enabled,
        is_phoenix_server_running,
    )
    server_up = is_phoenix_server_running()
    return {
        "langfuse_enabled": langfuse_on(),
        "phoenix_exporter_enabled": is_phoenix_enabled(),
        "phoenix_server_running": server_up,
        "phoenix_enabled": server_up,
        "phoenix_ui": get_phoenix_ui_url(),
        "phoenix_start_hint": "Run: phoenix serve  (or docker-compose up phoenix)",
        "local_traces": len(get_local_traces()),
    }


@router.get("/config")
async def get_config_summary() -> dict:
    cfg = get_platform_config()
    return {
        "platform": cfg.platform.get("platform", {}),
        "roles": cfg.list_roles(),
        "query_types": [qt["name"] for qt in cfg.get_query_types()],
        "connectors": [c.get("name") for c in cfg.get_connectors()],
        "connector_types": list_connector_types(),
        "graph_enabled": cfg.graph.get("enabled", False),
    }
