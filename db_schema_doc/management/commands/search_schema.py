from __future__ import annotations

import json

from db_schema_doc.management.command_utils import add_collect_arguments, collect_schema
from db_schema_doc.schema_search import format_hits_text, search_schema
from db_schema_doc.serialization import load_schema_dict
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Search the database schema by natural-language keywords "
        "(table/column names, model docs, business context, FKs)."
    )

    def add_arguments(self, parser):
        add_collect_arguments(parser)
        parser.add_argument(
            "query",
            nargs="+",
            help="Search terms (e.g. customer email order status).",
        )
        parser.add_argument(
            "--from-json",
            default="",
            metavar="PATH",
            help="Search a saved schema.json instead of introspecting the DB.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=25,
            help="Maximum number of hits (default: 25).",
        )
        parser.add_argument(
            "--min-score",
            type=float,
            default=1.0,
            help="Minimum relevance score to include a hit.",
        )
        parser.add_argument(
            "--format",
            choices=("text", "json"),
            default="text",
            help="Output format (default: text).",
        )
        parser.add_argument(
            "--to-stdout",
            action="store_true",
            dest="to_stdout",
            help="Print results to stdout (default for text format).",
        )

    def handle(self, *args, **options):
        query = " ".join(options["query"]).strip()
        if not query:
            raise CommandError("Provide at least one search term.")

        if options["from_json"]:
            schema = self._schema_from_json(options["from_json"], options)
        else:
            schema = collect_schema(self, options)

        hits = search_schema(
            schema,
            query,
            limit=options["limit"],
            min_score=options["min_score"],
        )

        if options["format"] == "json":
            payload = {
                "query": query,
                "hit_count": len(hits),
                "hits": [h.to_dict() for h in hits],
            }
            content = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        else:
            content = format_hits_text(hits, query=query)

        self.stdout.write(content)

    def _schema_from_json(self, path: str, options):
        from db_schema_doc.business_rules import (
            business_rules_enabled,
            enrich_schema_with_business_descriptions,
        )
        from db_schema_doc.collector import (
            BusinessDescription,
            ColumnInfo,
            DatabaseSchema,
            DjangoModelInfo,
            ForeignKeyInfo,
            IndexInfo,
            TableInfo,
        )
        from db_schema_doc.models_meta import enrich_schema_with_models

        data = load_schema_dict(path)
        tables: list[TableInfo] = []
        conn = data.get("connection", {})
        for raw in data.get("tables", []):
            django_model = None
            if raw.get("django_model"):
                dm = raw["django_model"]
                django_model = DjangoModelInfo(
                    app_label=dm["app_label"],
                    model_name=dm["model_name"],
                    verbose_name=dm.get("verbose_name", ""),
                    verbose_name_plural=dm.get("verbose_name_plural", ""),
                    doc=dm.get("doc", ""),
                )
            business = None
            if raw.get("business"):
                b = raw["business"]
                business = BusinessDescription(
                    description=b.get("description", ""),
                    sources=list(b.get("sources", [])),
                    hints=list(b.get("hints", [])),
                )
            columns = [
                ColumnInfo(
                    name=c["name"],
                    type_display=c["type_display"],
                    nullable=c["nullable"],
                    default=c.get("default"),
                    ordinal=c["ordinal"],
                    is_primary_key=c.get("is_primary_key", False),
                    django_field=c.get("django_field", ""),
                    verbose_name=c.get("verbose_name", ""),
                    help_text=c.get("help_text", ""),
                )
                for c in raw.get("columns", [])
            ]
            outgoing = [
                ForeignKeyInfo(**{k: fk.get(k, "") for k in (
                    "from_table", "from_column", "to_table", "to_column",
                    "constraint_name", "on_delete", "on_update",
                )})
                for fk in raw.get("outgoing_fks", [])
            ]
            incoming = [
                ForeignKeyInfo(**{k: fk.get(k, "") for k in (
                    "from_table", "from_column", "to_table", "to_column",
                    "constraint_name", "on_delete", "on_update",
                )})
                for fk in raw.get("incoming_fks", [])
            ]
            indexes = [
                IndexInfo(
                    name=i["name"],
                    columns=list(i.get("columns", [])),
                    unique=i.get("unique", False),
                )
                for i in raw.get("indexes", [])
            ]
            tables.append(
                TableInfo(
                    name=raw["name"],
                    schema=raw.get("schema", "dbo"),
                    columns=columns,
                    primary_key=list(raw.get("primary_key", [])),
                    outgoing_fks=outgoing,
                    incoming_fks=incoming,
                    indexes=indexes,
                    row_count=raw.get("row_count"),
                    django_model=django_model,
                    business=business,
                )
            )

        schema = DatabaseSchema(
            vendor=conn.get("vendor", ""),
            database_name=conn.get("database_name", ""),
            host=conn.get("host", ""),
            port=str(conn.get("port", "")),
            engine=conn.get("engine", ""),
            tables=tables,
        )
        if not options.get("no_model_metadata", False):
            enrich_schema_with_models(schema)
        if (
            not options.get("no_business_descriptions", False)
            and business_rules_enabled()
        ):
            enrich_schema_with_business_descriptions(schema)
        return schema
