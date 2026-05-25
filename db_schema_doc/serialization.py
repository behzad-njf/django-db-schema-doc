"""Serialize and deserialize DatabaseSchema for JSON export and diff."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .collector import (
    BusinessDescription,
    ColumnInfo,
    DatabaseSchema,
    DjangoModelInfo,
    ForeignKeyInfo,
    IndexInfo,
    QueryExample,
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
    payload: dict[str, Any] = {
        "name": table.name,
        "schema": table.schema,
        "primary_key": list(table.primary_key),
        "row_count": table.row_count,
        "columns": [_column_to_dict(c) for c in table.columns],
        "outgoing_fks": [_fk_to_dict(fk) for fk in table.outgoing_fks],
        "incoming_fks": [_fk_to_dict(fk) for fk in table.incoming_fks],
        "indexes": [_index_to_dict(idx) for idx in table.indexes],
    }
    if table.django_model is not None:
        payload["django_model"] = _django_model_to_dict(table.django_model)
    if table.business is not None:
        payload["business"] = _business_to_dict(table.business)
    if table.query_examples:
        payload["query_examples"] = [
            _query_example_to_dict(ex) for ex in table.query_examples
        ]
    return payload


def _query_example_to_dict(example: QueryExample) -> dict[str, Any]:
    return {
        "kind": example.kind,
        "title": example.title,
        "code": example.code,
        "related_tables": list(example.related_tables),
    }


def _business_to_dict(business: BusinessDescription) -> dict[str, Any]:
    return {
        "description": business.description,
        "sources": list(business.sources),
        "hints": list(business.hints),
    }


def _django_model_to_dict(model: DjangoModelInfo) -> dict[str, Any]:
    return {
        "app_label": model.app_label,
        "model_name": model.model_name,
        "verbose_name": model.verbose_name,
        "verbose_name_plural": model.verbose_name_plural,
        "doc": model.doc,
    }


def _column_to_dict(col: ColumnInfo) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": col.name,
        "type_display": col.type_display,
        "nullable": col.nullable,
        "default": col.default,
        "ordinal": col.ordinal,
        "is_primary_key": col.is_primary_key,
    }
    if col.django_field:
        payload["django_field"] = col.django_field
    if col.verbose_name:
        payload["verbose_name"] = col.verbose_name
    if col.help_text:
        payload["help_text"] = col.help_text
    return payload


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
