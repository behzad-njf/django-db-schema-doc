import json

import pytest

from db_schema_doc.collector import SchemaCollector
from db_schema_doc.exporters.ai_export import (
    AI_SCHEMA_VERSION,
    FORMAT_NAME,
    export_ai_schema_dict,
    export_ai_schema_json,
)
from db_schema_doc.models_meta import enrich_schema_with_models


@pytest.mark.django_db
def test_export_ai_schema_structure():
    schema = SchemaCollector().collect()
    enrich_schema_with_models(schema)
    data = export_ai_schema_dict(schema, database_alias="default", project_name="demo")

    assert data["ai_schema_version"] == AI_SCHEMA_VERSION
    assert data["format"] == FORMAT_NAME
    assert data["project_name"] == "demo"
    assert data["summary"]["table_count"] >= 4
    docs = data["documents"]
    assert docs[0]["kind"] == "overview"
    assert any(d["kind"] == "table" and d["table"] == "shop_order" for d in docs)
    assert any(d["kind"] == "foreign_key" for d in docs)


@pytest.mark.django_db
def test_table_chunk_includes_model_doc_and_columns():
    schema = SchemaCollector().collect()
    enrich_schema_with_models(schema)
    data = export_ai_schema_dict(schema)
    order = next(d for d in data["documents"] if d.get("table") == "shop_order")
    assert order["kind"] == "table"
    assert "Customer purchase" in order["content"]
    assert "shop.order" in order["content"]
    assert "Order status" in order["content"]
    assert order["metadata"]["django_model"] == "shop.order"


@pytest.mark.django_db
def test_no_fk_chunks_option():
    schema = SchemaCollector().collect()
    with_fk = export_ai_schema_dict(schema, include_fk_chunks=True)
    without_fk = export_ai_schema_dict(schema, include_fk_chunks=False)
    fk_with = sum(1 for d in with_fk["documents"] if d["kind"] == "foreign_key")
    fk_without = sum(1 for d in without_fk["documents"] if d["kind"] == "foreign_key")
    assert fk_with > 0
    assert fk_without == 0
    assert without_fk["summary"]["document_count"] < with_fk["summary"]["document_count"]


@pytest.mark.django_db
def test_export_ai_schema_json_roundtrip():
    schema = SchemaCollector().collect()
    enrich_schema_with_models(schema)
    raw = export_ai_schema_json(schema)
    parsed = json.loads(raw)
    assert parsed["format"] == FORMAT_NAME
    assert "documents" in parsed


@pytest.mark.django_db
def test_export_ai_schema_command(tmp_path, settings):
    from django.core.management import call_command

    settings.BASE_DIR = tmp_path
    out = tmp_path / "ai.json"
    call_command("export_ai_schema", output=str(out), project_name="shop-demo")
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["project_name"] == "shop-demo"
    assert any(d["table"] == "shop_order" for d in data["documents"] if d["kind"] == "table")
