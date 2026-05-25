"""Shared helpers for schema management commands."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from db_schema_doc.collector import DatabaseSchema, SchemaCollector


def add_collect_arguments(parser) -> None:
    """Arguments for introspection only (no output path)."""
    parser.add_argument(
        "--database",
        default="default",
        help="DATABASES alias to introspect (default: default).",
    )
    parser.add_argument(
        "--include-views",
        action="store_true",
        help="Include database views.",
    )
    parser.add_argument(
        "--with-row-counts",
        action="store_true",
        help="Run COUNT(*) per table (slow on large databases).",
    )


def add_common_schema_arguments(parser) -> None:
    parser.add_argument(
        "-o",
        "--output",
        default="",
        help="Output file path (default varies per command).",
    )
    add_collect_arguments(parser)
    parser.add_argument(
        "--to-stdout",
        action="store_true",
        dest="to_stdout",
        help="Write output to stdout instead of a file.",
    )


def collect_schema(command: BaseCommand, options) -> DatabaseSchema:
    database = options["database"]
    if database not in connections.databases:
        raise CommandError(
            f"Unknown database alias {database!r}. "
            f"Available: {', '.join(sorted(connections.databases))}"
        )
    command.stdout.write(f"Introspecting database {database!r}...")
    collector = SchemaCollector(
        database=database,
        include_views=options.get("include_views", False),
    )
    return collector.collect(row_counts=options.get("with_row_counts", False))


def resolve_output_path(output: str) -> Path:
    path = Path(output)
    if path.is_absolute():
        return path
    base = Path(getattr(settings, "BASE_DIR", Path.cwd()))
    return base / path


def write_text_output(
    command: BaseCommand,
    content: str,
    *,
    output: str,
    to_stdout: bool,
    success_message: str,
) -> None:
    if to_stdout:
        command.stdout.write(content)
        return
    output_path = resolve_output_path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    size_kb = output_path.stat().st_size / 1024
    command.stdout.write(command.style.SUCCESS(f"{success_message} ({size_kb:.1f} KB)"))
