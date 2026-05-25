from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command

from db_schema_doc.erd_bundle import erd_static_dir


@pytest.mark.django_db
def test_export_schema_json_command(tmp_path, settings):
    settings.BASE_DIR = tmp_path
    out = tmp_path / "out.json"
    call_command("export_schema_json", output=str(out))
    assert out.is_file()
    assert "shop_order" in out.read_text(encoding="utf-8")


@pytest.mark.django_db
def test_export_dbml_command(tmp_path, settings):
    settings.BASE_DIR = tmp_path
    out = tmp_path / "schema.dbml"
    call_command("export_dbml", output=str(out))
    assert "Table shop_order" in out.read_text(encoding="utf-8")


@pytest.mark.django_db
def test_schema_diff_command(tmp_path, settings):
    settings.BASE_DIR = tmp_path
    left = tmp_path / "left.json"
    right = tmp_path / "right.json"
    call_command("export_schema_json", output=str(left))
    call_command("export_schema_json", output=str(right))
    report = tmp_path / "diff.md"
    call_command("schema_diff", str(left), str(right), output=str(report))
    assert "No schema changes" in report.read_text(encoding="utf-8")


@pytest.mark.django_db
@pytest.mark.skipif(
    not (erd_static_dir() / "index.html").is_file(),
    reason="ERD static assets not built (npm run build in frontend/)",
)
def test_generate_erd_command(tmp_path, settings):
    settings.BASE_DIR = tmp_path
    out_dir = tmp_path / "erd"
    call_command("generate_erd", output=str(out_dir))
    assert (out_dir / "graph.json").is_file()
    assert (out_dir / "index.html").is_file()
    assert "shop_order" in (out_dir / "graph.json").read_text(encoding="utf-8")
