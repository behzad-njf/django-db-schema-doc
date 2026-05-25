"""
Merge Django ORM model metadata into a collected DatabaseSchema.

Maps each model's ``db_table`` to the matching ``TableInfo`` and fills
model docstrings, verbose names, and per-column field labels / help text.
"""

from __future__ import annotations

import inspect

from django.apps import apps
from django.db import models

from .collector import DatabaseSchema, DjangoModelInfo, TableInfo


def enrich_schema_with_models(schema: DatabaseSchema) -> int:
    """
    Attach Django model metadata to schema tables where a model exists.

    Returns the number of tables that were enriched.
    """
    table_by_name = {t.name: t for t in schema.tables}
    enriched = 0

    for model in apps.get_models(include_auto_created=True):
        db_table = model._meta.db_table
        table = table_by_name.get(db_table)
        if table is None:
            continue
        _apply_model_to_table(table, model)
        enriched += 1

    return enriched


def _apply_model_to_table(table: TableInfo, model: type[models.Model]) -> None:
    meta = model._meta
    table.django_model = DjangoModelInfo(
        app_label=meta.app_label,
        model_name=meta.model_name,
        verbose_name=str(meta.verbose_name),
        verbose_name_plural=str(meta.verbose_name_plural),
        doc=_clean_doc(inspect.getdoc(model)),
    )

    column_to_field: dict[str, models.Field] = {}
    for field in meta.get_fields():
        if not isinstance(field, models.Field):
            continue
        column = getattr(field, "column", None)
        if column:
            column_to_field[column] = field

    for col in table.columns:
        field = column_to_field.get(col.name)
        if field is None:
            continue
        col.django_field = field.name
        col.verbose_name = _field_verbose_name(field)
        col.help_text = _field_help_text(field)


def _clean_doc(doc: str | None) -> str:
    if not doc:
        return ""
    lines = [line.strip() for line in doc.strip().splitlines()]
    return "\n".join(line for line in lines if line)


def _field_verbose_name(field: models.Field) -> str:
    raw = str(getattr(field, "verbose_name", "") or "").strip()
    if not raw:
        return ""
    default = field.name.replace("_", " ")
    if raw == default:
        return ""
    return raw


def _field_help_text(field: models.Field) -> str:
    return str(getattr(field, "help_text", "") or "").strip()
