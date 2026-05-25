from __future__ import annotations

from db_schema_doc.erd_bundle import bundle_erd_output
from db_schema_doc.exporters.graph import export_graph_json
from db_schema_doc.management.command_utils import (
    add_collect_arguments,
    collect_schema,
    resolve_output_path,
)
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Generate interactive ERD (erd.html + graph.json + assets) "
        "using the bundled React Flow UI."
    )

    def add_arguments(self, parser):
        add_collect_arguments(parser)
        parser.add_argument(
            "-o",
            "--output",
            default="schema-erd",
            help="Output directory (default: schema-erd/ under BASE_DIR).",
        )

    def handle(self, *args, **options):
        schema = collect_schema(self, options)
        output_dir = resolve_output_path(options["output"] or "schema-erd")
        graph_json = export_graph_json(schema)

        try:
            written = bundle_erd_output(output_dir, graph_json)
        except FileNotFoundError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Wrote ERD to {output_dir} ({len(written)} paths). "
                f"Open {output_dir / 'index.html'} in a browser."
            )
        )
