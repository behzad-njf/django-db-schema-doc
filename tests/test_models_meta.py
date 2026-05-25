import json

import pytest

from db_schema_doc.collector import SchemaCollector
from db_schema_doc.models_meta import enrich_schema_with_models
from db_schema_doc.serialization import schema_to_dict
from db_schema_doc.writer import MarkdownWriter


@pytest.mark.django_db
def test_enrich_attaches_shop_order_model_doc():
    schema = SchemaCollector().collect()
    assert enrich_schema_with_models(schema) >= 4

    order = next(t for t in schema.tables if t.name == "shop_order")
    assert order.django_model is not None
    assert order.django_model.app_label == "shop"
    assert order.django_model.model_name == "order"
    assert "Customer purchase" in order.django_model.doc

    status_col = next(c for c in order.columns if c.name == "status")
    assert status_col.django_field == "status"
    assert status_col.verbose_name == "Order status"
    assert "pending" in status_col.help_text


@pytest.mark.django_db
def test_markdown_includes_business_description():
    schema = SchemaCollector().collect()
    enrich_schema_with_models(schema)
    md = MarkdownWriter(schema, title="Test").write()
    assert "**Django model:** `shop.order`" in md
    assert "**Business description (model):**" in md
    assert "Customer purchase" in md
    assert "Order status" in md


@pytest.mark.django_db
def test_json_export_includes_django_model():
    schema = SchemaCollector().collect()
    enrich_schema_with_models(schema)
    data = schema_to_dict(schema)
    order = next(t for t in data["tables"] if t["name"] == "shop_order")
    assert order["django_model"]["doc"]
    status = next(c for c in order["columns"] if c["name"] == "status")
    assert status["verbose_name"] == "Order status"


@pytest.mark.django_db
def test_no_enrich_when_skipped_via_collect():
    from django.core.management import call_command
    from io import StringIO

    out = StringIO()
    call_command(
        "export_schema_json",
        "--to-stdout",
        "--no-model-metadata",
        stdout=out,
    )
    data = json.loads(out.getvalue())
    order = next(t for t in data["tables"] if t["name"] == "shop_order")
    assert "django_model" not in order
