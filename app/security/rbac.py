"""Config-driven RBAC enforcement at retrieval time."""

from app.models.schemas import DocumentMetadata
from app.platform.config_loader import get_platform_config


def get_effective_roles(role: str) -> set[str]:
    cfg = get_platform_config()
    return cfg.get_effective_roles(role)


def is_authorized(metadata: DocumentMetadata, role: str) -> bool:
    effective = get_effective_roles(role)
    return bool(effective.intersection(set(metadata.allowed_roles)))


def filter_authorized_doc_ids(
    all_metadata: dict[str, DocumentMetadata],
    role: str,
) -> set[str]:
    return {
        doc_id
        for doc_id, meta in all_metadata.items()
        if is_authorized(meta, role)
    }


def build_rbac_filter(role: str) -> dict:
    return {"allowed_roles": list(get_effective_roles(role))}
