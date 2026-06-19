"""Config-driven knowledge graph using NetworkX."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import networkx as nx

from app.config import get_settings
from app.platform.config_loader import get_platform_config


class KnowledgeGraph:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.graph = nx.DiGraph()
            cls._instance._loaded = False
        return cls._instance

    def build_from_sql(self, db_path: Path) -> None:
        cfg = get_platform_config()
        if not cfg.graph.get("enabled", True):
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        for mapping in cfg.graph.get("entity_mappings", []):
            table = mapping.get("table")
            try:
                cursor.execute(f"SELECT * FROM {table}")
                columns = [d[0] for d in cursor.description]
                rows = cursor.fetchall()
            except Exception:
                continue

            for row in rows:
                row_dict = dict(zip(columns, row))
                node_id = self._format_template(
                    mapping.get("id_template") or f"{table}_{{{mapping.get('id_field', columns[0])}}}",
                    row_dict,
                )
                props = {p: row_dict.get(p) for p in mapping.get("properties", [])}
                props["type"] = mapping.get("entity_type", table)
                self.graph.add_node(node_id, **props)

                for rel in mapping.get("relationships", []):
                    from_node = node_id
                    if "from" in rel:
                        from_node = self._format_template(rel["from"], row_dict)
                    target = self._format_template(rel["target_template"], row_dict)
                    self.graph.add_node(
                        target,
                        type=rel.get("target_type", "Entity"),
                        name=row_dict.get(rel.get("target_type", "").lower(), target),
                    )
                    self.graph.add_edge(from_node, target, relation=rel.get("relation", "linked"))

        conn.close()

    def _format_template(self, template: str, row: dict) -> str:
        result = template
        for key, val in row.items():
            safe_val = str(val).replace(" ", "_").lower() if val else ""
            result = result.replace(f"{{{key}}}", safe_val)
        return result

    def save(self) -> None:
        path = Path(get_settings().graph_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(nx.node_link_data(self.graph)), encoding="utf-8")

    def load(self) -> None:
        if self._loaded:
            return
        path = Path(get_settings().graph_path)
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            self.graph = nx.node_link_graph(data, directed=True)
        self._loaded = True

    def multi_hop_query(self, query: str) -> list[str]:
        cfg = get_platform_config()
        if not cfg.graph.get("enabled", True):
            return []

        self.load()
        context_lines: list[str] = []
        q = query.lower()

        for rule in cfg.graph.get("query_expansion", []):
            keywords = rule.get("match_keywords", [])
            if keywords and not all(kw in q for kw in keywords):
                continue

            entity_type = rule.get("entity_type")
            for node, data in self.graph.nodes(data=True):
                if data.get("type") != entity_type:
                    continue

                if rule.get("filter_property"):
                    prop_val = str(data.get(rule["filter_property"], ""))
                    if rule.get("filter_equals") and prop_val != rule["filter_equals"]:
                        continue
                    if rule.get("filter_contains") and rule["filter_contains"] not in prop_val:
                        continue

                if rule.get("expand") == "predecessors":
                    team_key = q.replace(" ", "_")
                    if team_key.replace("_", " ") not in q and node not in q:
                        continue
                    for pred in self.graph.predecessors(node):
                        pdata = self.graph.nodes[pred]
                        context_lines.append(
                            rule.get("template", "{node_id}").format(
                                node_id=pred,
                                entity_type=pdata.get("type", "unknown"),
                                **pdata,
                            )
                        )
                else:
                    context_lines.append(
                        rule.get("template", "{node_id}").format(node_id=node, **data)
                    )

        return context_lines
