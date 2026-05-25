"""JSON schema snapshot export."""

from __future__ import annotations

from db_schema_doc.collector import DatabaseSchema
from db_schema_doc.serialization import schema_to_json

__all__ = ["export_schema_json"]


def export_schema_json(
    schema: DatabaseSchema,
    *,
    database_alias: str = "default",
    indent: int = 2,
) -> str:
    return schema_to_json(schema, database_alias=database_alias, indent=indent)
