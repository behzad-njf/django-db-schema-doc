"""Shared helpers for schema management commands."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from db_schema_doc.collector import DatabaseSchema, SchemaCollector
from db_schema_doc.business_rules import (
    business_rules_enabled,
    enrich_schema_with_business_descriptions,
)
from db_schema_doc.models_meta import enrich_schema_with_models
from db_schema_doc.query_examples import (
    enrich_schema_with_query_examples,
    query_examples_enabled,
)


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
    parser.add_argument(
        "--no-model-metadata",
        action="store_true",
        help="Skip merging Django model docstrings and field labels into the schema.",
    )
    parser.add_argument(
        "--no-business-descriptions",
        action="store_true",
        help="Skip rule-based business descriptions (domain, FK roles, column hints).",
    )
    parser.add_argument(
        "--no-query-examples",
        action="store_true",
        help="Skip SQL / ORM query example generation.",
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
    command.stderr.write(f"Introspecting database {database!r}...\n")
    collector = SchemaCollector(
        database=database,
        include_views=options.get("include_views", False),
    )
    schema = collector.collect(row_counts=options.get("with_row_counts", False))
    if not options.get("no_model_metadata", False):
        n = enrich_schema_with_models(schema)
        if n:
            command.stderr.write(
                f"Merged Django model metadata for {n} table(s).\n"
            )
    if (
        not options.get("no_business_descriptions", False)
        and business_rules_enabled()
    ):
        n = enrich_schema_with_business_descriptions(schema)
        if n:
            command.stderr.write(
                f"Applied business rules to {n} table(s).\n"
            )
    if (
        not options.get("no_query_examples", False)
        and query_examples_enabled()
    ):
        n = enrich_schema_with_query_examples(schema)
        if n:
            command.stderr.write(
                f"Generated query examples for {n} table(s).\n"
            )
    return schema


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
