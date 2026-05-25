import json

import pytest

from db_schema_doc.collector import SchemaCollector
from db_schema_doc.business_rules import enrich_schema_with_business_descriptions
from db_schema_doc.models_meta import enrich_schema_with_models
from db_schema_doc.query_examples import build_query_examples, enrich_schema_with_query_examples
from db_schema_doc.serialization import schema_to_dict
from db_schema_doc.writer import MarkdownWriter


def _full_schema():
    schema = SchemaCollector().collect()
    enrich_schema_with_models(schema)
    enrich_schema_with_business_descriptions(schema)
    enrich_schema_with_query_examples(schema)
    return schema


@pytest.mark.django_db
def test_order_has_sql_and_orm_examples():
    schema = _full_schema()
    order = next(t for t in schema.tables if t.name == "shop_order")
    kinds = {ex.kind for ex in order.query_examples}
    assert "sql" in kinds
    assert "orm" in kinds
    codes = "\n".join(ex.code for ex in order.query_examples)
    assert "shop_order" in codes
    assert "Order.objects" in codes
    assert "select_related('customer')" in codes


@pytest.mark.django_db
def test_orderitem_join_sql():
    schema = _full_schema()
    item = next(t for t in schema.tables if t.name == "shop_orderitem")
    codes = "\n".join(ex.code for ex in item.query_examples)
    assert "shop_order" in codes
    assert "shop_product" in codes


@pytest.mark.django_db
def test_markdown_includes_query_examples():
    schema = _full_schema()
    md = MarkdownWriter(schema, title="Test").write()
    assert "**Query examples:**" in md
    assert "Order.objects.select_related" in md
    assert "```sql" in md
    assert "```python" in md


@pytest.mark.django_db
def test_json_export_includes_query_examples():
    schema = _full_schema()
    data = schema_to_dict(schema)
    order = next(t for t in data["tables"] if t["name"] == "shop_order")
    assert order["query_examples"]
    assert order["query_examples"][0]["kind"] in ("sql", "orm")


@pytest.mark.django_db
def test_export_schema_examples_command():
    from io import StringIO

    from django.core.management import call_command

    buf = StringIO()
    call_command("export_schema_examples", "--to-stdout", stdout=buf)
    data = json.loads(buf.getvalue())
    assert data["examples_version"] == 1
    tables = {t["table"]: t for t in data["tables"]}
    assert "shop_order" in tables
    assert any(ex["kind"] == "orm" for ex in tables["shop_order"]["examples"])


@pytest.mark.django_db
def test_no_examples_when_disabled():
    from django.core.management import call_command
    from io import StringIO

    schema = SchemaCollector().collect()
    enrich_schema_with_models(schema)
    examples = build_query_examples(next(t for t in schema.tables if t.name == "shop_order"))
    assert examples

    buf = StringIO()
    call_command(
        "export_schema_json",
        "--to-stdout",
        "--no-query-examples",
        stdout=buf,
    )
    data = json.loads(buf.getvalue())
    order = next(t for t in data["tables"] if t["name"] == "shop_order")
    assert "query_examples" not in order
