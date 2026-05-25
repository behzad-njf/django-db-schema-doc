from __future__ import annotations

from django.conf import settings

from db_schema_doc.exporters.ai_export import export_ai_schema_json
from db_schema_doc.management.command_utils import (
    add_common_schema_arguments,
    collect_schema,
    write_text_output,
)
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Export schema as RAG-friendly JSON: text chunks per table and "
        "foreign key, with metadata for vector search / agents."
    )

    def add_arguments(self, parser):
        add_common_schema_arguments(parser)
        parser.set_defaults(output="ai_schema.json")
        parser.add_argument(
            "--project-name",
            default="",
            help="Project label in overview chunk (default: database name).",
        )
        parser.add_argument(
            "--no-fk-chunks",
            action="store_true",
            help="Omit separate foreign_key documents (FKs still appear in table chunks).",
        )

    def handle(self, *args, **options):
        schema = collect_schema(self, options)
        project_name = options["project_name"] or None
        if project_name is None:
            project_name = getattr(settings, "PROJECT_NAME", None) or None

        content = export_ai_schema_json(
            schema,
            database_alias=options["database"],
            project_name=project_name,
            include_fk_chunks=not options["no_fk_chunks"],
        )
        write_text_output(
            self,
            content,
            output=options["output"] or "ai_schema.json",
            to_stdout=options["to_stdout"],
            success_message=f"Wrote {options['output'] or 'ai_schema.json'}",
        )
