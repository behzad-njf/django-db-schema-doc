"""
AI / RAG-oriented schema export: embeddable text chunks with structured metadata.

Each document has a stable ``id``, human-readable ``content`` for vector search,
and ``metadata`` for filtering (table name, domain, Django model path, etc.).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from db_schema_doc.collector import DatabaseSchema, ForeignKeyInfo, TableInfo
from db_schema_doc.writer import infer_domain

AI_SCHEMA_VERSION = 1
FORMAT_NAME = "django-db-schema-doc-ai-schema"

__all__ = [
    "AI_SCHEMA_VERSION",
    "export_ai_schema_dict",
    "export_ai_schema_json",
]


def export_ai_schema_dict(
    schema: DatabaseSchema,
    *,
    database_alias: str = "default",
    project_name: str | None = None,
    include_fk_chunks: bool = True,
) -> dict[str, Any]:
    project = project_name or schema.database_name
    documents: list[dict[str, Any]] = []

    documents.append(_overview_document(schema, project=project))
    for table in sorted(schema.tables, key=lambda t: t.name):
        documents.append(_table_document(table))
        if include_fk_chunks:
            for fk in table.outgoing_fks:
                documents.append(_foreign_key_document(fk))

    return {
        "ai_schema_version": AI_SCHEMA_VERSION,
        "format": FORMAT_NAME,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database_alias": database_alias,
        "project_name": project,
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
            "document_count": len(documents),
            "domains": _domain_counts(schema),
        },
        "documents": documents,
    }


def export_ai_schema_json(
    schema: DatabaseSchema,
    *,
    database_alias: str = "default",
    project_name: str | None = None,
    include_fk_chunks: bool = True,
    indent: int = 2,
) -> str:
    payload = export_ai_schema_dict(
        schema,
        database_alias=database_alias,
        project_name=project_name,
        include_fk_chunks=include_fk_chunks,
    )
    return json.dumps(payload, indent=indent, ensure_ascii=False) + "\n"


def _domain_counts(schema: DatabaseSchema) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in schema.tables:
        dom = infer_domain(table.name)
        counts[dom] = counts.get(dom, 0) + 1
    return dict(sorted(counts.items()))


def _overview_document(schema: DatabaseSchema, *, project: str) -> dict[str, Any]:
    domains = _domain_counts(schema)
    domain_lines = ", ".join(f"{k} ({v} tables)" for k, v in domains.items())
    lines = [
        f"Database schema overview for project {project!r}.",
        f"Engine: {schema.engine} ({schema.vendor}).",
        f"Database: {schema.database_name}.",
        f"Tables: {len(schema.tables)}; columns: {schema.column_count}; "
        f"foreign keys: {schema.fk_count}.",
    ]
    if domain_lines:
        lines.append(f"Domains: {domain_lines}.")
    lines.append(
        "Use table documents for column lists and Django model descriptions; "
        "use foreign_key documents for join paths."
    )
    return {
        "id": "overview",
        "kind": "overview",
        "title": f"{project} schema overview",
        "content": "\n".join(lines),
        "metadata": {
            "table_count": len(schema.tables),
            "domains": domains,
        },
    }


def _table_title(table: TableInfo) -> str:
    if table.django_model is not None:
        dm = table.django_model
        label = dm.verbose_name or dm.model_name
        return f"{table.name} ({label})"
    return table.name


def _table_document(table: TableInfo) -> dict[str, Any]:
    dom = infer_domain(table.name)
    lines = [f"Table `{table.name}` in domain `{dom}`."]

    if table.django_model is not None:
        dm = table.django_model
        lines.append(f"Django model: `{dm.app_label}.{dm.model_name}`.")
        if dm.verbose_name:
            lines.append(f"Model label: {dm.verbose_name}.")
        if dm.doc:
            lines.append(dm.doc)

    if table.business is not None:
        if table.business.description:
            lines.append(f"Inferred context: {table.business.description}")
        for hint in table.business.hints:
            lines.append(hint)

    if table.query_examples:
        lines.append("Query examples:")
        for ex in table.query_examples[:6]:
            lines.append(f"- {ex.title} ({ex.kind}): {ex.code.replace(chr(10), ' ')}")

    if table.primary_key:
        lines.append(f"Primary key columns: {', '.join(table.primary_key)}.")
    else:
        lines.append("No primary key defined.")

    if table.row_count is not None:
        lines.append(f"Approximate row count: {table.row_count}.")

    lines.append("Columns:")
    for col in table.columns:
        pk = " [PK]" if col.is_primary_key else ""
        null = "nullable" if col.nullable else "required"
        parts = [f"- `{col.name}`{pk}: {col.type_display} ({null})"]
        if col.django_field:
            parts.append(f"django field `{col.django_field}`")
        if col.verbose_name:
            parts.append(f"label {col.verbose_name!r}")
        if col.help_text:
            parts.append(f"help: {col.help_text}")
        if col.default:
            parts.append(f"default {col.default!r}")
        lines.append(" ".join(parts))

    if table.outgoing_fks:
        lines.append("Outgoing foreign keys:")
        for fk in table.outgoing_fks:
            lines.append(_fk_sentence(fk))

    if table.incoming_fks:
        lines.append("Referenced by:")
        for fk in table.incoming_fks:
            lines.append(
                f"- `{fk.from_table}.{fk.from_column}` → `{table.name}.{fk.to_column}`"
            )

    if table.indexes:
        lines.append("Indexes:")
        for idx in table.indexes:
            uniq = "unique " if idx.unique else ""
            cols = ", ".join(idx.columns)
            lines.append(f"- `{idx.name}` ({uniq}): {cols}")

    metadata: dict[str, Any] = {
        "table": table.name,
        "domain": dom,
        "primary_key": list(table.primary_key),
        "column_count": len(table.columns),
        "fk_out_count": len(table.outgoing_fks),
        "fk_in_count": len(table.incoming_fks),
    }
    if table.django_model is not None:
        dm = table.django_model
        metadata["django_model"] = f"{dm.app_label}.{dm.model_name}"
        if dm.doc:
            metadata["has_model_doc"] = True
    if table.business is not None:
        metadata["business_sources"] = list(table.business.sources)

    return {
        "id": f"table:{table.name}",
        "kind": "table",
        "table": table.name,
        "domain": dom,
        "title": _table_title(table),
        "content": "\n".join(lines),
        "metadata": metadata,
    }


def _foreign_key_document(fk: ForeignKeyInfo) -> dict[str, Any]:
    chunk_id = (
        f"fk:{fk.from_table}.{fk.from_column}->{fk.to_table}.{fk.to_column}"
    )
    lines = [
        _fk_sentence(fk),
        f"Join `{fk.from_table}` to `{fk.to_table}` on "
        f"`{fk.from_table}.{fk.from_column}` = `{fk.to_table}.{fk.to_column}`.",
    ]
    if fk.on_delete or fk.on_update:
        rules = []
        if fk.on_delete:
            rules.append(f"ON DELETE {fk.on_delete}")
        if fk.on_update:
            rules.append(f"ON UPDATE {fk.on_update}")
        lines.append("Referential rules: " + ", ".join(rules) + ".")

    metadata: dict[str, Any] = {
        "from_table": fk.from_table,
        "from_column": fk.from_column,
        "to_table": fk.to_table,
        "to_column": fk.to_column,
        "from_domain": infer_domain(fk.from_table),
        "to_domain": infer_domain(fk.to_table),
    }
    if fk.constraint_name:
        metadata["constraint_name"] = fk.constraint_name

    return {
        "id": chunk_id,
        "kind": "foreign_key",
        "title": f"{fk.from_table}.{fk.from_column} → {fk.to_table}.{fk.to_column}",
        "content": "\n".join(lines),
        "metadata": metadata,
    }


def _fk_sentence(fk: ForeignKeyInfo) -> str:
    rules = ""
    if fk.on_delete or fk.on_update:
        parts = []
        if fk.on_delete:
            parts.append(f"ON DELETE {fk.on_delete}")
        if fk.on_update:
            parts.append(f"ON UPDATE {fk.on_update}")
        rules = " (" + ", ".join(parts) + ")"
    return (
        f"- `{fk.from_column}` → `{fk.to_table}.{fk.to_column}`{rules}"
    )
