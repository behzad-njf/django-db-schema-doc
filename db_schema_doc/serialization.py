"""Serialize and deserialize DatabaseSchema for JSON export and diff."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .collector import (
    ColumnInfo,
    DatabaseSchema,
    ForeignKeyInfo,
    IndexInfo,
    TableInfo,
)

SCHEMA_VERSION = 1


def schema_to_dict(
    schema: DatabaseSchema,
    *,
    database_alias: str = "default",
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "database_alias": database_alias,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "connection": {
            "engine": schema.engine,
            "vendor": schema.vendor,
            "database_name": schema.database_name,
            "host": schema.host,
            "port": schema.port,
        },
        "summary": {
            "table_count": len(schema.tables),
            "column_count": schema.column_count,
            "fk_count": schema.fk_count,
        },
        "tables": [_table_to_dict(t) for t in sorted(schema.tables, key=lambda x: x.name)],
    }


def schema_to_json(
    schema: DatabaseSchema,
    *,
    database_alias: str = "default",
    indent: int = 2,
) -> str:
    return json.dumps(
        schema_to_dict(schema, database_alias=database_alias),
        indent=indent,
        ensure_ascii=False,
    ) + "\n"


def load_schema_dict(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported schema_version {data.get('schema_version')!r}; "
            f"expected {SCHEMA_VERSION}."
        )
    return data


def _table_to_dict(table: TableInfo) -> dict[str, Any]:
    return {
        "name": table.name,
        "schema": table.schema,
        "primary_key": list(table.primary_key),
        "row_count": table.row_count,
        "columns": [_column_to_dict(c) for c in table.columns],
        "outgoing_fks": [_fk_to_dict(fk) for fk in table.outgoing_fks],
        "incoming_fks": [_fk_to_dict(fk) for fk in table.incoming_fks],
        "indexes": [_index_to_dict(idx) for idx in table.indexes],
    }


def _column_to_dict(col: ColumnInfo) -> dict[str, Any]:
    return {
        "name": col.name,
        "type_display": col.type_display,
        "nullable": col.nullable,
        "default": col.default,
        "ordinal": col.ordinal,
        "is_primary_key": col.is_primary_key,
    }


def _fk_to_dict(fk: ForeignKeyInfo) -> dict[str, Any]:
    return {
        "from_table": fk.from_table,
        "from_column": fk.from_column,
        "to_table": fk.to_table,
        "to_column": fk.to_column,
        "constraint_name": fk.constraint_name,
        "on_delete": fk.on_delete,
        "on_update": fk.on_update,
    }


def _index_to_dict(idx: IndexInfo) -> dict[str, Any]:
    return {
        "name": idx.name,
        "columns": list(idx.columns),
        "unique": idx.unique,
    }
