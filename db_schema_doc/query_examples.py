"""
Rule-based SQL and Django ORM query examples from schema metadata.
"""

from __future__ import annotations

from django.apps import apps
from django.conf import settings
from django.db import models

from .collector import DatabaseSchema, ForeignKeyInfo, QueryExample, TableInfo

MAX_JOIN_EXAMPLES = 3
MAX_REVERSE_ORM_EXAMPLES = 2


def query_examples_enabled() -> bool:
    cfg = getattr(settings, "DB_SCHEMA_DOC", None)
    if isinstance(cfg, dict):
        return bool(cfg.get("QUERY_EXAMPLES", True))
    return True


def enrich_schema_with_query_examples(schema: DatabaseSchema) -> int:
    """Attach ``TableInfo.query_examples`` for each table. Returns table count."""
    enriched = 0
    for table in schema.tables:
        examples = build_query_examples(table)
        if examples:
            table.query_examples = examples
            enriched += 1
    return enriched


def build_query_examples(table: TableInfo) -> list[QueryExample]:
    examples = _sql_examples(table)
    if table.django_model is not None:
        try:
            model = apps.get_model(
                table.django_model.app_label,
                table.django_model.model_name,
            )
        except LookupError:
            return examples
        examples.extend(_orm_examples(model, table))
    return examples


def _sql_examples(table: TableInfo) -> list[QueryExample]:
    name = table.name
    examples: list[QueryExample] = [
        QueryExample(
            kind="sql",
            title="List rows",
            code=f"SELECT *\nFROM {name}\nLIMIT 100;",
        ),
        QueryExample(
            kind="sql",
            title="Count rows",
            code=f"SELECT COUNT(*) AS total\nFROM {name};",
        ),
    ]

    pk = table.primary_key
    if len(pk) == 1:
        col = pk[0]
        examples.append(
            QueryExample(
                kind="sql",
                title="Fetch by primary key",
                code=(
                    f"SELECT *\nFROM {name}\n"
                    f"WHERE {col} = 1;"
                ),
            )
        )

    status_col = _find_column(table, ("status", "state", "phase"))
    if status_col:
        examples.append(
            QueryExample(
                kind="sql",
                title=f"Filter by {status_col}",
                code=(
                    f"SELECT *\nFROM {name}\n"
                    f"WHERE {status_col} = 'pending';"
                ),
            )
        )

    for index, fk in enumerate(table.outgoing_fks[:MAX_JOIN_EXAMPLES]):
        alias = "t"
        ref = f"ref{index + 1}" if index else "ref"
        examples.append(
            QueryExample(
                kind="sql",
                title=f"Join {fk.to_table}",
                code=(
                    f"SELECT {alias}.*, {ref}.*\n"
                    f"FROM {name} AS {alias}\n"
                    f"INNER JOIN {fk.to_table} AS {ref}\n"
                    f"  ON {alias}.{fk.from_column} = {ref}.{fk.to_column};"
                ),
                related_tables=[fk.to_table],
            )
        )

    if len(table.outgoing_fks) >= 2:
        examples.append(_sql_multi_join(table))

    return examples


def _sql_multi_join(table: TableInfo) -> QueryExample:
    alias = "t"
    lines = [f"SELECT {alias}.*"]
    joins: list[str] = [f"FROM {table.name} AS {alias}"]
    related: list[str] = []
    for index, fk in enumerate(table.outgoing_fks[:MAX_JOIN_EXAMPLES]):
        ref = f"r{index + 1}"
        lines[0] += f", {ref}.*"
        joins.append(
            f"INNER JOIN {fk.to_table} AS {ref}\n"
            f"  ON {alias}.{fk.from_column} = {ref}.{fk.to_column}"
        )
        related.append(fk.to_table)
    return QueryExample(
        kind="sql",
        title="Join related tables",
        code="\n".join(lines + joins) + ";",
        related_tables=related,
    )


def _orm_examples(model: type[models.Model], table: TableInfo) -> list[QueryExample]:
    class_name = model.__name__
    import_path = f"{model._meta.app_label}.models"
    examples: list[QueryExample] = [
        QueryExample(
            kind="orm",
            title="Import model",
            code=f"from {import_path} import {class_name}",
        ),
        QueryExample(
            kind="orm",
            title="List all",
            code=f"{class_name}.objects.all()",
        ),
    ]

    pk_name = model._meta.pk.name if model._meta.pk else None
    if pk_name:
        examples.append(
            QueryExample(
                kind="orm",
                title="Get by primary key",
                code=f'{class_name}.objects.get(pk=1)',
            )
        )

    fk_fields = [
        f
        for f in model._meta.fields
        if isinstance(f, (models.ForeignKey, models.OneToOneField))
    ][:MAX_JOIN_EXAMPLES]
    for field in fk_fields:
        related_table = field.remote_field.model._meta.db_table
        attname = getattr(field, "attname", f"{field.name}_id")
        examples.append(
            QueryExample(
                kind="orm",
                title=f"With {field.name} (select_related)",
                code=(
                    f"{class_name}.objects.select_related('{field.name}').all()"
                ),
                related_tables=[related_table],
            )
        )
        examples.append(
            QueryExample(
                kind="orm",
                title=f"Filter by {field.name}",
                code=f"{class_name}.objects.filter({attname}=1)",
                related_tables=[related_table],
            )
        )

    reverse_added = 0
    for field in model._meta.get_fields():
        if not field.auto_created or field.concrete:
            continue
        if field.many_to_many:
            if reverse_added >= MAX_REVERSE_ORM_EXAMPLES:
                break
            accessor = field.get_accessor_name()
            examples.append(
                QueryExample(
                    kind="orm",
                    title=f"Prefetch {accessor}",
                    code=f"{class_name}.objects.prefetch_related('{accessor}')",
                )
            )
            reverse_added += 1
        elif field.one_to_many:
            if reverse_added >= MAX_REVERSE_ORM_EXAMPLES:
                break
            accessor = field.get_accessor_name()
            examples.append(
                QueryExample(
                    kind="orm",
                    title=f"With related {accessor}",
                    code=f"{class_name}.objects.prefetch_related('{accessor}')",
                )
            )
            reverse_added += 1

    status_field = _find_django_field(model, ("status", "state", "phase"))
    if status_field:
        examples.append(
            QueryExample(
                kind="orm",
                title=f"Filter by {status_field}",
                code=f'{class_name}.objects.filter({status_field}="pending")',
            )
        )

    return examples


def _find_column(table: TableInfo, names: tuple[str, ...]) -> str | None:
    for col in table.columns:
        if col.name.lower() in names:
            return col.name
    return None


def _find_django_field(model: type[models.Model], names: tuple[str, ...]) -> str | None:
    for field in model._meta.fields:
        if field.name in names:
            return field.name
    return None


def examples_export_dict(schema: DatabaseSchema) -> dict:
    return {
        "examples_version": 1,
        "table_count": len(schema.tables),
        "tables": [
            {
                "table": table.name,
                "django_model": (
                    f"{table.django_model.app_label}.{table.django_model.model_name}"
                    if table.django_model
                    else None
                ),
                "examples": [
                    {
                        "kind": ex.kind,
                        "title": ex.title,
                        "code": ex.code,
                        "related_tables": list(ex.related_tables),
                    }
                    for ex in table.query_examples
                ],
            }
            for table in sorted(schema.tables, key=lambda t: t.name)
            if table.query_examples
        ],
    }
