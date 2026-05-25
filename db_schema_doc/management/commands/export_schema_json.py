from __future__ import annotations

from db_schema_doc.exporters.json_export import export_schema_json
from db_schema_doc.management.command_utils import (
    add_common_schema_arguments,
    collect_schema,
    write_text_output,
)
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Export database schema as JSON snapshot (schema_version 1)."

    def add_arguments(self, parser):
        add_common_schema_arguments(parser)
        parser.set_defaults(output="schema.json")

    def handle(self, *args, **options):
        schema = collect_schema(self, options)
        content = export_schema_json(schema, database_alias=options["database"])
        write_text_output(
            self,
            content,
            output=options["output"] or "schema.json",
            to_stdout=options["to_stdout"],
            success_message=f"Wrote {options['output'] or 'schema.json'}",
        )
