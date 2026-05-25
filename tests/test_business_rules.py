import json

import pytest

from db_schema_doc.business_rules import enrich_schema_with_business_descriptions, infer_table_business
from db_schema_doc.collector import SchemaCollector
from db_schema_doc.models_meta import enrich_schema_with_models
from db_schema_doc.serialization import schema_to_dict
from db_schema_doc.writer import MarkdownWriter


def _full_schema():
    schema = SchemaCollector().collect()
    enrich_schema_with_models(schema)
    enrich_schema_with_business_descriptions(schema)
    return schema


@pytest.mark.django_db
def test_orderitem_gets_junction_and_fk_hints():
    schema = _full_schema()
    item = next(t for t in schema.tables if t.name == "shop_orderitem")
    assert item.business is not None
    assert "junction_table" in item.business.sources
    assert "order" in item.business.description.lower()
    assert any("shop_order" in h for h in item.business.hints)


@pytest.mark.django_db
def test_customer_model_doc_and_fk_hints():
    schema = _full_schema()
    customer = next(t for t in schema.tables if t.name == "shop_customer")
    assert customer.django_model and "People who place" in customer.django_model.doc
    assert customer.business is not None
    assert any("shop_order" in h for h in customer.business.hints)
    md = MarkdownWriter(schema, title="Test").write()
    assert "**Business description (model):**" in md
    assert "**Inferred business context:**" in md
    assert "shop` business domain" in md


@pytest.mark.django_db
def test_order_child_of_customer():
    schema = _full_schema()
    order = next(t for t in schema.tables if t.name == "shop_order")
    assert order.business is not None
    assert "child_table" in order.business.sources
    assert "shop_customer" in order.business.description


@pytest.mark.django_db
def test_markdown_business_only_when_no_model_doc():
    schema = SchemaCollector().collect()
    enrich_schema_with_business_descriptions(schema)
    item = next(t for t in schema.tables if t.name == "shop_orderitem")
    biz = infer_table_business(item, schema)
    assert biz.description
    md = MarkdownWriter(schema, title="Test").write()
    assert "### `shop_orderitem`" in md
    idx = md.index("### `shop_orderitem`")
    section = md[idx : idx + 1200]
    assert "**Business description:**" in section
    assert "**Business description (model):**" not in section.split("### `shop_product`")[0]


@pytest.mark.django_db
def test_json_includes_business_block():
    schema = _full_schema()
    data = schema_to_dict(schema)
    order = next(t for t in data["tables"] if t["name"] == "shop_order")
    assert "business" in order
    assert order["business"]["description"]
    assert "domain" in order["business"]["sources"]


@pytest.mark.django_db
def test_no_business_when_flagged():
    from django.core.management import call_command

    from io import StringIO

    schema = SchemaCollector().collect()
    enrich_schema_with_models(schema)
    enrich_schema_with_business_descriptions(schema)
    assert schema.tables[0].business is not None

    out = StringIO()
    call_command(
        "export_schema_json",
        "--to-stdout",
        "--no-business-descriptions",
        stdout=out,
    )
    data = json.loads(out.getvalue())
    order = next(t for t in data["tables"] if t["name"] == "shop_order")
    assert "business" not in order


@pytest.mark.django_db
def test_ai_schema_includes_inferred_context():
    from db_schema_doc.exporters.ai_export import export_ai_schema_dict

    schema = _full_schema()
    data = export_ai_schema_dict(schema)
    item = next(d for d in data["documents"] if d.get("table") == "shop_orderitem")
    assert "Inferred context:" in item["content"]
    assert "Associates or details" in item["content"]
