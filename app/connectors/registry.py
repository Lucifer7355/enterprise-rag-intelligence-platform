"""Connector plugin registry — auto-discovers built-in and custom connectors."""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from typing import Type

from app.connectors.base import BaseConnector
from app.observability.logging import get_logger

logger = get_logger(__name__)

_REGISTRY: dict[str, Type[BaseConnector]] = {}


def register_connector(connector_type: str, cls: Type[BaseConnector]) -> None:
    _REGISTRY[connector_type] = cls


def get_connector_class(connector_type: str) -> Type[BaseConnector] | None:
    return _REGISTRY.get(connector_type)


def list_connector_types() -> list[str]:
    return list(_REGISTRY.keys())


def create_connector(config: dict) -> BaseConnector | None:
    connector_type = config.get("type")
    cls = get_connector_class(connector_type)
    if cls is None:
        logger.warning("unknown_connector_type", type=connector_type, name=config.get("name"))
        return None
    return cls(config)


def _register_builtin_connectors() -> None:
    from app.connectors import (
        csv_connector,
        folder_connector,
        inline_connector,
        json_connector,
        pdf_connector,
        sql_connector,
    )

    for module in [folder_connector, pdf_connector, csv_connector, json_connector, sql_connector, inline_connector]:
        for attr in dir(module):
            obj = getattr(module, attr)
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseConnector)
                and obj is not BaseConnector
                and hasattr(obj, "connector_type")
            ):
                register_connector(obj.connector_type, obj)


def _load_plugin_connectors() -> None:
    """Scan plugins/connectors/ for custom connector modules."""
    plugins_dir = Path(__file__).resolve().parent.parent.parent / "plugins" / "connectors"
    if not plugins_dir.exists():
        return

    for module_info in pkgutil.iter_modules([str(plugins_dir)]):
        try:
            module = importlib.import_module(f"plugins.connectors.{module_info.name}")
            for attr in dir(module):
                obj = getattr(module, attr)
                if (
                    isinstance(obj, type)
                    and issubclass(obj, BaseConnector)
                    and obj is not BaseConnector
                    and hasattr(obj, "connector_type")
                ):
                    register_connector(obj.connector_type, obj)
                    logger.info("plugin_connector_loaded", type=obj.connector_type, module=module_info.name)
        except Exception as e:
            logger.warning("plugin_connector_failed", module=module_info.name, error=str(e))


def initialize_registry() -> None:
    if _REGISTRY:
        return
    _register_builtin_connectors()
    _load_plugin_connectors()
