"""Export SQL / ORM query examples as JSON."""

from __future__ import annotations

import json

from db_schema_doc.collector import DatabaseSchema
from db_schema_doc.query_examples import examples_export_dict

__all__ = ["export_examples_json"]


def export_examples_json(schema: DatabaseSchema, *, indent: int = 2) -> str:
    payload = examples_export_dict(schema)
    return json.dumps(payload, indent=indent, ensure_ascii=False) + "\n"
