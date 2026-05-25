import pytest

from db_schema_doc.collector import SchemaCollector


@pytest.mark.django_db
def test_collects_shop_tables():
    schema = SchemaCollector().collect()
    names = {t.name for t in schema.tables}
    assert "shop_customer" in names
    assert "shop_order" in names
    assert "shop_orderitem" in names
    assert "shop_product" in names


@pytest.mark.django_db
def test_order_has_outgoing_foreign_keys():
    schema = SchemaCollector().collect()
    order = next(t for t in schema.tables if t.name == "shop_order")
    assert order.outgoing_fks
    targets = {fk.to_table for fk in order.outgoing_fks}
    assert "shop_customer" in targets


@pytest.mark.django_db
def test_schema_metadata():
    schema = SchemaCollector().collect()
    assert schema.vendor == "sqlite"
    assert schema.column_count > 0
    assert schema.fk_count >= 3
