import pytest

from db_schema_doc.collector import SchemaCollector
from db_schema_doc.writer import MarkdownWriter, hub_tables, infer_domain


def test_infer_domain_shop_prefix():
    assert infer_domain("shop_order") == "shop"


def test_infer_domain_django_system():
    assert infer_domain("django_session") == "django_system"


@pytest.mark.django_db
def test_markdown_writer_includes_shop_tables():
    schema = SchemaCollector().collect()
    md = MarkdownWriter(schema, title="Test Schema").write()
    assert "# Test Schema" in md
    assert "shop_order" in md
    assert "Foreign keys:" in md
    assert "## 4. Hub tables" in md


@pytest.mark.django_db
def test_hub_tables_ranks_referenced_tables():
    schema = SchemaCollector().collect()
    hubs = hub_tables(schema, limit=5)
    assert hubs
    names = [h[0] for h in hubs]
    assert "shop_customer" in names or "shop_order" in names
