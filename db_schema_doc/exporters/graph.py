"""Graph JSON for interactive ERD (React Flow)."""

from __future__ import annotations

import json
from typing import Any

from db_schema_doc.collector import DatabaseSchema
from db_schema_doc.serialization import SCHEMA_VERSION, _table_to_dict
from db_schema_doc.writer import infer_domain

__all__ = ["export_graph_dict", "export_graph_json"]


def export_graph_dict(schema: DatabaseSchema) -> dict[str, Any]:
    domains: dict[str, list[str]] = {}
    for table in schema.tables:
        dom = infer_domain(table.name)
        domains.setdefault(dom, []).append(table.name)

    nodes: list[dict[str, Any]] = []
    x_offset = 0.0
    for dom in sorted(domains.keys()):
        tables = sorted(domains[dom])
        for index, name in enumerate(tables):
            table = next(t for t in schema.tables if t.name == name)
            nodes.append(
                {
                    "id": name,
                    "type": "table",
                    "position": {
                        "x": x_offset + (index % 4) * 280,
                        "y": (index // 4) * 200,
                    },
                    "data": {
                        "label": name,
                        "domain": dom,
                        "column_count": len(table.columns),
                        "fk_out": len(table.outgoing_fks),
                        "fk_in": len(table.incoming_fks),
                        "table": _table_to_dict(table),
                    },
                }
            )
        x_offset += 320.0

    edges: list[dict[str, Any]] = []
    edge_id = 0
    for table in schema.tables:
        for fk in table.outgoing_fks:
            edges.append(
                {
                    "id": f"e{edge_id}",
                    "source": fk.from_table,
                    "target": fk.to_table,
                    "label": fk.from_column,
                    "data": {
                        "from_column": fk.from_column,
                        "to_column": fk.to_column,
                        "on_delete": fk.on_delete,
                        "on_update": fk.on_update,
                    },
                }
            )
            edge_id += 1

    return {
        "schema_version": SCHEMA_VERSION,
        "database_name": schema.database_name,
        "vendor": schema.vendor,
        "nodes": nodes,
        "edges": edges,
    }


def export_graph_json(schema: DatabaseSchema, *, indent: int = 2) -> str:
    return json.dumps(export_graph_dict(schema), indent=indent, ensure_ascii=False) + "\n"
