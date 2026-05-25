import json

import pytest

from db_schema_doc.collector import SchemaCollector
from db_schema_doc.business_rules import enrich_schema_with_business_descriptions
from db_schema_doc.models_meta import enrich_schema_with_models
from db_schema_doc.schema_search import (
    format_hits_text,
    search_schema,
    tokenize_query,
)


def _full_schema():
    schema = SchemaCollector().collect()
    enrich_schema_with_models(schema)
    enrich_schema_with_business_descriptions(schema)
    return schema


@pytest.mark.django_db
def test_tokenize_strips_stopwords():
    assert tokenize_query("find the customer email") == ["customer", "email"]


@pytest.mark.django_db
def test_search_customer_email():
    schema = _full_schema()
    hits = search_schema(schema, "customer email")
    tables = {h.table for h in hits}
    assert "shop_customer" in tables
    kinds = {h.kind for h in hits}
    assert "column" in kinds or "table" in kinds


@pytest.mark.django_db
def test_search_order_status_synonym():
    schema = _full_schema()
    hits = search_schema(schema, "order status")
    assert any(h.table == "shop_order" for h in hits)


@pytest.mark.django_db
def test_search_foreign_key_finds_relationships():
    schema = _full_schema()
    hits = search_schema(schema, "foreign key customer")
    assert any(h.table == "shop_order" for h in hits)
    assert all(h.kind == "foreign_key" for h in hits)


@pytest.mark.django_db
def test_search_junction_orderitem():
    schema = _full_schema()
    hits = search_schema(schema, "order product")
    assert any(h.table == "shop_orderitem" for h in hits)


@pytest.mark.django_db
def test_format_hits_text_empty():
    assert "No matches" in format_hits_text([], query="zzz")


@pytest.mark.django_db
def test_search_schema_command_json():
    from io import StringIO

    from django.core.management import call_command

    buf = StringIO()
    call_command(
        "search_schema",
        "customer",
        "email",
        "--format",
        "json",
        stdout=buf,
    )
    data = json.loads(buf.getvalue())
    assert data["hit_count"] >= 1
    assert any(h["table"] == "shop_customer" for h in data["hits"])


@pytest.mark.django_db
def test_search_schema_from_json_file(tmp_path, settings):
    from django.core.management import call_command

    settings.BASE_DIR = tmp_path
    snapshot = tmp_path / "schema.json"
    call_command("export_schema_json", output=str(snapshot))

    from io import StringIO

    buf = StringIO()
    call_command(
        "search_schema",
        "shop",
        "order",
        "--from-json",
        str(snapshot),
        "--format",
        "json",
        stdout=buf,
    )
    data = json.loads(buf.getvalue())
    assert any(h["table"] == "shop_order" for h in data["hits"])
