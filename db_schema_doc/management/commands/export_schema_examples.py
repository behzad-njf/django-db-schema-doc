from __future__ import annotations

from db_schema_doc.exporters.examples_export import export_examples_json
from db_schema_doc.management.command_utils import (
    add_common_schema_arguments,
    collect_schema,
    write_text_output,
)
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Export rule-generated SQL and Django ORM query examples per table."
    )

    def add_arguments(self, parser):
        add_common_schema_arguments(parser)
        parser.set_defaults(output="schema_examples.json")

    def handle(self, *args, **options):
        schema = collect_schema(self, options)
        content = export_examples_json(schema)
        write_text_output(
            self,
            content,
            output=options["output"] or "schema_examples.json",
            to_stdout=options["to_stdout"],
            success_message=f"Wrote {options['output'] or 'schema_examples.json'}",
        )
