from __future__ import annotations

from pathlib import Path

from db_schema_doc.diff.compare import compare_schema_dicts
from db_schema_doc.diff.report import diff_to_json, diff_to_markdown
from db_schema_doc.management.command_utils import resolve_output_path, write_text_output
from db_schema_doc.serialization import load_schema_dict
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Compare two JSON schema snapshots (optional schema diff tool)."

    def add_arguments(self, parser):
        parser.add_argument("left", help="Path to left/baseline schema JSON.")
        parser.add_argument("right", help="Path to right/new schema JSON.")
        parser.add_argument(
            "-o",
            "--output",
            default="SCHEMA_DIFF.md",
            help="Output report path (default: SCHEMA_DIFF.md).",
        )
        parser.add_argument(
            "--format",
            choices=["markdown", "json"],
            default="markdown",
            help="Report format (default: markdown).",
        )
        parser.add_argument(
            "--to-stdout",
            action="store_true",
            dest="to_stdout",
            help="Print report to stdout.",
        )

    def handle(self, *args, **options):
        left_path = Path(options["left"])
        right_path = Path(options["right"])
        if not left_path.is_file():
            raise CommandError(f"Left schema file not found: {left_path}")
        if not right_path.is_file():
            raise CommandError(f"Right schema file not found: {right_path}")

        left = load_schema_dict(str(left_path))
        right = load_schema_dict(str(right_path))
        diff = compare_schema_dicts(left, right)

        if options["format"] == "json":
            content = diff_to_json(diff)
        else:
            content = diff_to_markdown(
                diff,
                left_label=str(left_path),
                right_label=str(right_path),
            )

        output = options["output"]
        if options["format"] == "json" and output == "SCHEMA_DIFF.md":
            output = "schema_diff.json"

        write_text_output(
            self,
            content,
            output=output,
            to_stdout=options["to_stdout"],
            success_message=f"Wrote {output}" + (" (no changes)" if not diff.has_changes else ""),
        )
