"""
Management command: generate DATABASE.md (or custom path) from the configured database.

Portable across Django projects — add ``db_schema_doc`` to INSTALLED_APPS (or copy
this package into your project) and run::

    python manage.py generate_database_doc

See db_schema_doc/README.md for setup in other projects.
"""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from db_schema_doc.collector import SchemaCollector
from db_schema_doc.writer import MarkdownWriter


class Command(BaseCommand):
    help = (
        "Generate Markdown database schema documentation (DATABASE.md) "
        "from the configured Django database connection."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "-o",
            "--output",
            default="DATABASE.md",
            help="Output Markdown file path (default: DATABASE.md in project root).",
        )
        parser.add_argument(
            "--database",
            default="default",
            help="DATABASES alias to introspect (default: default).",
        )
        parser.add_argument(
            "--title",
            default="",
            help="Document title (default: '<db_name> Database Schema Reference').",
        )
        parser.add_argument(
            "--include-views",
            action="store_true",
            help="Include database views in the documentation.",
        )
        parser.add_argument(
            "--with-row-counts",
            action="store_true",
            help="Run COUNT(*) per table (slow on large databases).",
        )
        parser.add_argument(
            "--hub-limit",
            type=int,
            default=25,
            help="Number of hub tables to list in the overview (default: 25).",
        )
        parser.add_argument(
            "--no-fk-index",
            action="store_true",
            help="Omit the foreign-key relationship index section.",
        )
        parser.add_argument(
            "--no-hub-section",
            action="store_true",
            help="Omit the hub-tables overview section.",
        )
        parser.add_argument(
            "--project-hints",
            default="",
            help="Optional Markdown paragraph with project-specific notes for agents.",
        )
        parser.add_argument(
            "--to-stdout",
            action="store_true",
            dest="to_stdout",
            help="Print Markdown to stdout instead of writing a file.",
        )

    def handle(self, *args, **options):
        database = options["database"]
        if database not in connections.databases:
            raise CommandError(
                f"Unknown database alias {database!r}. "
                f"Available: {', '.join(sorted(connections.databases))}"
            )

        self.stdout.write(f"Introspecting database {database!r}...")
        collector = SchemaCollector(
            database=database,
            include_views=options["include_views"],
        )
        schema = collector.collect(row_counts=options["with_row_counts"])

        title = options["title"] or None
        hints = options["project_hints"] or None
        writer = MarkdownWriter(
            schema,
            title=title,
            include_fk_index=not options["no_fk_index"],
            include_hub_section=not options["no_hub_section"],
            hub_limit=options["hub_limit"],
            project_hints=hints,
        )
        markdown = writer.write()

        if options["to_stdout"]:
            self.stdout.write(markdown)
            return

        output_path = self._resolve_output_path(options["output"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")

        size_kb = output_path.stat().st_size / 1024
        self.stdout.write(
            self.style.SUCCESS(
                f"Wrote {output_path} "
                f"({len(schema.tables)} tables, {schema.column_count} columns, "
                f"{schema.fk_count} FKs, {size_kb:.1f} KB)"
            )
        )

    def _resolve_output_path(self, output: str) -> Path:
        path = Path(output)
        if path.is_absolute():
            return path
        base = Path(getattr(settings, "BASE_DIR", Path.cwd()))
        return base / path
