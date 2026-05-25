"""Copy built ERD static assets into an output directory."""

from __future__ import annotations

import shutil
from importlib import resources
from pathlib import Path


def erd_static_dir() -> Path:
    """Directory containing pre-built Vite output (index.html + assets/)."""
    return Path(resources.files("db_schema_doc")).joinpath("static", "erd")


def bundle_erd_output(output_dir: Path, graph_json: str) -> list[Path]:
    """
    Write graph.json and copy ERD UI assets into output_dir.
    Returns list of paths written.
    """
    static = erd_static_dir()
    if not static.is_dir() or not (static / "index.html").is_file():
        raise FileNotFoundError(
            "ERD static assets not found. Build the frontend:\n"
            "  cd db_schema_doc/frontend && npm install && npm run build"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    graph_path = output_dir / "graph.json"
    graph_path.write_text(graph_json, encoding="utf-8")
    written.append(graph_path)

    for item in static.iterdir():
        dest = output_dir / item.name
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
        written.append(dest)

    return written
