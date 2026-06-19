"""Unit tests for connector plugin system."""

from app.connectors.registry import initialize_registry, list_connector_types, create_connector
from app.platform.config_loader import get_platform_config


def test_builtin_connectors_registered():
    initialize_registry()
    types = list_connector_types()
    assert "folder" in types
    assert "sql" in types
    assert "csv" in types
    assert "json" in types
    assert "inline" in types


def test_connectors_loaded_from_config():
    cfg = get_platform_config()
    connectors = cfg.get_connectors()
    assert len(connectors) >= 1
    names = [c["name"] for c in connectors]
    assert "enterprise_sql" in names


def test_create_connector_from_config():
    initialize_registry()
    cfg = get_platform_config()
    connector_cfg = cfg.get_connector_by_name("financial_csv")
    assert connector_cfg is not None
    connector = create_connector(connector_cfg)
    assert connector is not None
    docs = connector.fetch()
    assert len(docs) > 0
