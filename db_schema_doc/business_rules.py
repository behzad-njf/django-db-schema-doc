"""
Rule-based business descriptions for schema tables (no LLM).

Heuristics use naming, foreign keys, column patterns, and Django model labels
to infer how a table fits in the domain. Model docstrings (Phase 2.1) stay
separate; rules add structural and domain context.
"""

from __future__ import annotations

import re

from django.conf import settings

from .collector import BusinessDescription, ColumnInfo, DatabaseSchema, TableInfo
from .writer import infer_domain

# Incoming FK count to treat a table as a hub (referenced by many others).
HUB_INCOMING_FK_THRESHOLD = 2

# Framework table name hints (prefix -> short role).
DJANGO_SYSTEM_ROLES: tuple[tuple[str, str], ...] = (
    ("django_session", "Stores user session keys for authentication."),
    ("django_migrations", "Records applied Django schema migrations."),
    ("django_content_type", "Maps models to content types for permissions."),
    ("django_admin_log", "Audit log of actions in the Django admin."),
    ("auth_user", "User accounts for authentication."),
    ("auth_group", "Named groups for permission assignment."),
    ("auth_permission", "Permissions attached to models or groups."),
    ("auth_", "Authentication / authorization data."),
    ("django_", "Django framework internal data."),
)

# Column suffix/name -> hint text.
COLUMN_PATTERN_HINTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^(created|updated|modified|deleted)_at$"), "Includes audit timestamps."),
    (re.compile(r"^deleted_at$"), "Supports soft-delete (row may be hidden, not removed)."),
    (re.compile(r"^(email|e_mail)$"), "Stores an email address."),
    (re.compile(r"^(status|state|phase)$"), "Tracks workflow or lifecycle state."),
    (re.compile(r"^(price|amount|total|cost|fee)$"), "Monetary or quantity amount field."),
    (re.compile(r"^(sku|code|slug)$"), "Business identifier or catalog code."),
)


def business_rules_enabled() -> bool:
    cfg = getattr(settings, "DB_SCHEMA_DOC", None)
    if isinstance(cfg, dict):
        return bool(cfg.get("BUSINESS_RULES", True))
    return True


def enrich_schema_with_business_descriptions(schema: DatabaseSchema) -> int:
    """
    Attach rule-based ``TableInfo.business`` for each table.

    Returns the number of tables that received a non-empty description.
    """
    enriched = 0
    for table in schema.tables:
        business = infer_table_business(table, schema)
        if business.description or business.hints:
            table.business = business
            enriched += 1
    return enriched


def infer_table_business(table: TableInfo, schema: DatabaseSchema) -> BusinessDescription:
    domain = infer_domain(table.name)
    sources: list[str] = []
    hints: list[str] = []
    sentences: list[str] = []

    if domain == "django_system":
        role = _django_system_role(table.name)
        if role:
            sentences.append(role)
            sources.append("django_system")
    elif domain != "other":
        sentences.append(f"Part of the `{domain}` business domain.")
        sources.append("domain")

    entity = _humanize_entity(_entity_suffix(table.name, domain))
    if entity and domain != "django_system":
        sentences.append(f"Entity focus: {entity}.")
        sources.append("table_name")

    if table.django_model is not None and not table.django_model.doc:
        dm = table.django_model
        label = dm.verbose_name_plural or dm.verbose_name or dm.model_name
        sentences.append(f"Stores {label} records.")
        sources.append("model_label")

    junction = _is_junction_table(table)
    if junction:
        targets = [
            _humanize_entity(_entity_suffix(fk.to_table, infer_domain(fk.to_table)))
            for fk in table.outgoing_fks
        ]
        pair = " and ".join(targets[:2])
        sentences.append(f"Associates or details links between {pair}.")
        sources.append("junction_table")

    in_count = len(table.incoming_fks)
    if in_count >= HUB_INCOMING_FK_THRESHOLD:
        sentences.append(
            f"Central reference table ({in_count} tables reference it via foreign keys)."
        )
        sources.append("hub_table")
    elif len(table.outgoing_fks) == 1 and not junction:
        fk = table.outgoing_fks[0]
        parent = _humanize_entity(
            _entity_suffix(fk.to_table, infer_domain(fk.to_table))
        )
        sentences.append(f"Child or detail rows belonging to `{fk.to_table}` ({parent}).")
        sources.append("child_table")

    for fk in table.outgoing_fks:
        target_entity = _humanize_entity(
            _entity_suffix(fk.to_table, infer_domain(fk.to_table))
        )
        hints.append(
            f"Links to `{fk.to_table}` ({target_entity}) via `{fk.from_column}`."
        )
        if "fk_links" not in sources:
            sources.append("fk_links")

    for fk in table.incoming_fks:
        child_entity = _humanize_entity(
            _entity_suffix(fk.from_table, infer_domain(fk.from_table))
        )
        hints.append(
            f"Referenced by `{fk.from_table}` ({child_entity}) via `{fk.from_column}`."
        )
        if "fk_incoming" not in sources:
            sources.append("fk_incoming")

    col_hints = _column_pattern_hints(table.columns)
    for hint in col_hints:
        if hint not in hints:
            hints.append(hint)
    if col_hints and "column_patterns" not in sources:
        sources.append("column_patterns")

    description = " ".join(sentences).strip()
    return BusinessDescription(
        description=description,
        sources=sources,
        hints=hints,
    )


def _django_system_role(table_name: str) -> str:
    for prefix, role in DJANGO_SYSTEM_ROLES:
        if table_name == prefix or (
            prefix.endswith("_") and table_name.startswith(prefix)
        ):
            return role
    return "Django or project framework table (not application business data)."


def _entity_suffix(table_name: str, domain: str) -> str:
    if domain in ("other", "django_system"):
        return table_name
    prefix = f"{domain}_"
    if table_name.startswith(prefix):
        return table_name[len(prefix) :]
    return table_name


def _humanize_entity(suffix: str) -> str:
    if not suffix:
        return ""
    parts = suffix.split("_")
    return " ".join(parts)


def _is_junction_table(table: TableInfo) -> bool:
    fk_count = len(table.outgoing_fks)
    if fk_count < 2:
        return False
    fk_columns = {fk.from_column for fk in table.outgoing_fks}
    non_fk_cols = [
        c
        for c in table.columns
        if c.name not in fk_columns and not c.is_primary_key
    ]
    return len(non_fk_cols) <= 2


def _column_pattern_hints(columns: list[ColumnInfo]) -> list[str]:
    seen: list[str] = []
    for col in columns:
        name = col.name.lower()
        for pattern, hint in COLUMN_PATTERN_HINTS:
            if pattern.search(name) and hint not in seen:
                seen.append(hint)
    return seen
