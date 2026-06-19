"""Config-driven source router."""

from app.platform.config_loader import get_platform_config


def route_sources(query_type: str, query: str) -> list[str]:
    cfg = get_platform_config()
    sources: list[str] = []

    for qt in cfg.get_query_types():
        if qt.get("name") == query_type:
            raw_sources = qt.get("sources", ["*"])
            if "*" in raw_sources:
                sources = _all_source_types(cfg)
            else:
                sources = list(raw_sources)
            break

    if not sources:
        sources = _all_source_types(cfg)

    q = query.lower()
    for rule in cfg.routing.get("multi_hop_rules", []):
        keywords = rule.get("match_all", [])
        if keywords and all(kw in q for kw in keywords):
            sources.extend(rule.get("add_sources", []))

    return list(dict.fromkeys(sources))


def _all_source_types(cfg) -> list[str]:
    types = set()
    for connector in cfg.get_connectors():
        meta = connector.get("metadata", {})
        if ds := meta.get("data_source"):
            types.add(ds)
        for table_cfg in connector.get("tables", {}).values():
            if ds := table_cfg.get("metadata", {}).get("data_source"):
                types.add(ds)
    return list(types) or ["*"]
