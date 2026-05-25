"""Export DatabaseSchema as DBML (https://dbml.dbdiagram.io/docs/)."""

from __future__ import annotations

import re

from db_schema_doc.collector import DatabaseSchema, TableInfo

# Django introspection type_display -> DBML type (best effort)
_TYPE_MAP = {
    "AutoField": "int",
    "BigAutoField": "bigint",
    "BigIntegerField": "bigint",
    "BinaryField": "blob",
    "BooleanField": "boolean",
    "CharField": "varchar",
    "DateField": "date",
    "DateTimeField": "datetime",
    "DecimalField": "decimal",
    "DurationField": "varchar",
    "EmailField": "varchar",
    "FilePathField": "varchar",
    "FloatField": "float",
    "IntegerField": "int",
    "GenericIPAddressField": "varchar",
    "JSONField": "json",
    "PositiveBigIntegerField": "bigint",
    "PositiveIntegerField": "int",
    "PositiveSmallIntegerField": "int",
    "SlugField": "varchar",
    "SmallAutoField": "int",
    "SmallIntegerField": "int",
    "TextField": "text",
    "TimeField": "time",
    "URLField": "varchar",
    "UUIDField": "uuid",
    "ForeignKey": "int",
    "ForeignKeyField": "int",
}


def export_dbml(schema: DatabaseSchema) -> str:
    lines: list[str] = [
        f"// Generated from {schema.database_name} ({schema.vendor})",
        "",
    ]
    for table in sorted(schema.tables, key=lambda t: t.name):
        lines.extend(_table_dbml(table))
        lines.append("")
    lines.extend(_ref_lines(schema))
    return "\n".join(lines).rstrip() + "\n"


def _table_dbml(table: TableInfo) -> list[str]:
    lines = [f"Table {_quote_ident(table.name)} {{"]
    for col in table.columns:
        dbml_type = _TYPE_MAP.get(col.type_display, "varchar")
        settings: list[str] = []
        if col.is_primary_key:
            settings.append("pk")
        if not col.nullable:
            settings.append("not null")
        if col.default:
            settings.append(f"default: `{_escape_note(col.default)}`")
        if col.type_display not in _TYPE_MAP:
            settings.append(f'note: "{_escape_note(col.type_display)}"')
        setting_str = f" [{', '.join(settings)}]" if settings else ""
        lines.append(f"  {_quote_ident(col.name)} {dbml_type}{setting_str}")
    lines.append("}")
    return lines


def _ref_lines(schema: DatabaseSchema) -> list[str]:
    lines: list[str] = []
    seen: set[tuple[str, str, str, str]] = set()
    for table in schema.tables:
        for fk in table.outgoing_fks:
            key = (fk.from_table, fk.from_column, fk.to_table, fk.to_column)
            if key in seen:
                continue
            seen.add(key)
            ref = (
                f"Ref: {_quote_ident(fk.from_table)}.{_quote_ident(fk.from_column)} "
                f"> {_quote_ident(fk.to_table)}.{_quote_ident(fk.to_column)}"
            )
            lines.append(ref)
    return lines


def _quote_ident(name: str) -> str:
    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
        return name
    return f'"{name.replace(chr(34), "")}"'


def _escape_note(text: str) -> str:
    return text.replace('"', "'")[:120]
