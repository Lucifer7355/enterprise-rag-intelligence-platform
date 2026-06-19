"""Unit tests for config-driven RBAC."""

from app.models.schemas import DocumentMetadata
from app.platform.config_loader import get_platform_config
from app.security.rbac import filter_authorized_doc_ids, is_authorized


def test_finance_can_access_finance_docs():
    meta = DocumentMetadata(
        document_id="fin1",
        source="revenue.csv",
        department="finance",
        allowed_roles=["Finance", "Admin"],
    )
    assert is_authorized(meta, "Finance")
    assert not is_authorized(meta, "Engineering")


def test_admin_can_access_all():
    meta = DocumentMetadata(
        document_id="hr1",
        source="HR_Policies.pdf",
        department="hr",
        allowed_roles=["HR"],
    )
    assert is_authorized(meta, "Admin")


def test_filter_authorized_docs():
    metadata = {
        "fin1": DocumentMetadata(
            document_id="fin1", source="a", department="finance", allowed_roles=["Finance"]
        ),
        "eng1": DocumentMetadata(
            document_id="eng1", source="b", department="engineering", allowed_roles=["Engineering"]
        ),
    }
    authorized = filter_authorized_doc_ids(metadata, "Finance")
    assert "fin1" in authorized
    assert "eng1" not in authorized


def test_roles_loaded_from_config():
    cfg = get_platform_config()
    assert "Admin" in cfg.list_roles()
    assert "Engineering" in cfg.list_roles()
