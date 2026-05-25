import json

import pytest

from db_schema_doc.collector import SchemaCollector
from db_schema_doc.diff.compare import compare_schema_dicts
from db_schema_doc.exporters.dbml import export_dbml
from db_schema_doc.exporters.graph import export_graph_dict
from db_schema_doc.exporters.json_export import export_schema_json
from db_schema_doc.serialization import load_schema_dict


@pytest.mark.django_db
def test_export_schema_json_structure():
    schema = SchemaCollector().collect()
    raw = export_schema_json(schema, database_alias="default")
    data = json.loads(raw)
    assert data["schema_version"] == 1
    assert data["connection"]["vendor"] == "sqlite"
    assert any(t["name"] == "shop_order" for t in data["tables"])


@pytest.mark.django_db
def test_export_dbml_contains_tables_and_refs():
    schema = SchemaCollector().collect()
    dbml = export_dbml(schema)
    assert "Table shop_order" in dbml
    assert "Ref:" in dbml
    assert "shop_customer" in dbml


@pytest.mark.django_db
def test_export_graph_nodes_and_edges():
    schema = SchemaCollector().collect()
    graph = export_graph_dict(schema)
    assert len(graph["nodes"]) >= 4
    assert any(e["source"] == "shop_order" for e in graph["edges"])
    order_node = next(n for n in graph["nodes"] if n["id"] == "shop_order")
    assert "table" in order_node["data"]
    assert order_node["data"]["table"]["columns"]


def test_schema_diff_detects_table_added(tmp_path):
    left = {
        "schema_version": 1,
        "tables": [{"name": "a", "columns": [], "outgoing_fks": [], "incoming_fks": [], "indexes": [], "primary_key": []}],
    }
    right = {
        "schema_version": 1,
        "tables": [
            {"name": "a", "columns": [], "outgoing_fks": [], "incoming_fks": [], "indexes": [], "primary_key": []},
            {"name": "b", "columns": [], "outgoing_fks": [], "incoming_fks": [], "indexes": [], "primary_key": []},
        ],
    }
    diff = compare_schema_dicts(left, right)
    assert diff.tables_added == ["b"]
    assert diff.has_changes


def test_load_schema_dict_version_check(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"schema_version": 99, "tables": []}', encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported schema_version"):
        load_schema_dict(str(path))
