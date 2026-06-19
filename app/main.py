"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.api.auth_routes import router as auth_router
from app.api.routes import router
from app.config import get_settings
from app.connectors.registry import initialize_registry
from app.ingestion.pipeline import IngestionPipeline
from app.observability.langfuse_client import init_langfuse
from app.observability.logging import setup_logging, get_logger
from app.observability.phoenix_setup import init_phoenix
from app.platform.config_loader import get_platform_config

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings = get_settings()
    initialize_registry()
    cfg = get_platform_config()

    phoenix_ok = init_phoenix()
    langfuse_ok = init_langfuse()

    logger.info(
        "app_starting",
        host=settings.api_host,
        port=settings.api_port,
        roles=cfg.list_roles(),
        connectors=len(cfg.get_connectors()),
        phoenix=phoenix_ok,
        langfuse=langfuse_ok,
    )

    platform_cfg = cfg.platform.get("platform", {})
    if platform_cfg.get("auto_ingest_on_startup", True):
        try:
            if platform_cfg.get("sample_data_enabled", True):
                from scripts.generate_synthetic_data import main as generate_data
                generate_data()
            IngestionPipeline().run()
            logger.info("auto_ingestion_complete")
        except Exception as e:
            logger.warning("auto_ingestion_skipped", error=str(e))

    yield
    logger.info("app_shutdown")


app = FastAPI(
    title="Enterprise RAG Intelligence Platform",
    description="Production RAG with auth, SSO, Langfuse, Phoenix, and live RAGAS",
    version="2.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(router)
FastAPIInstrumentor.instrument_app(app)


@app.get("/health")
async def health():
    from app.observability.langfuse_client import is_enabled as langfuse_on
    from app.observability.phoenix_setup import is_phoenix_enabled
    from app.security.auth import is_auth_enabled

    cfg = get_platform_config()
    return {
        "status": "healthy",
        "service": "enterprise-rag",
        "mode": "production-ready",
        "auth_enabled": is_auth_enabled(),
        "langfuse": langfuse_on(),
        "phoenix": is_phoenix_enabled(),
        "connectors": len(cfg.get_connectors()),
        "roles": len(cfg.list_roles()),
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.api_host, port=settings.api_port, reload=True)
