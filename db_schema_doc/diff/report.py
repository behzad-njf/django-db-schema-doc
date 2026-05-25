"""Render SchemaDiff as Markdown or JSON."""

from __future__ import annotations

import json
from typing import Any

from .compare import SchemaDiff


def diff_to_markdown(diff: SchemaDiff, *, left_label: str, right_label: str) -> str:
    lines = [
        "# Schema diff report",
        "",
        f"- **Left:** {left_label}",
        f"- **Right:** {right_label}",
        "",
    ]
    if not diff.has_changes:
        lines.append("No schema changes detected.")
        return "\n".join(lines) + "\n"

    if diff.tables_added:
        lines.append("## Tables added")
        for name in diff.tables_added:
            lines.append(f"- `{name}`")
        lines.append("")

    if diff.tables_removed:
        lines.append("## Tables removed")
        for name in diff.tables_removed:
            lines.append(f"- `{name}`")
        lines.append("")

    if diff.columns_added:
        lines.append("## Columns added")
        for table, cols in sorted(diff.columns_added.items()):
            lines.append(f"### `{table}`")
            for col in cols:
                lines.append(f"- `{col}`")
            lines.append("")

    if diff.columns_removed:
        lines.append("## Columns removed")
        for table, cols in sorted(diff.columns_removed.items()):
            lines.append(f"### `{table}`")
            for col in cols:
                lines.append(f"- `{col}`")
            lines.append("")

    if diff.columns_changed:
        lines.append("## Columns changed")
        for table, changes in sorted(diff.columns_changed.items()):
            lines.append(f"### `{table}`")
            for ch in changes:
                lines.append(
                    f"- `{ch['column']}`: {ch['left_type']} → {ch['right_type']} "
                    f"(nullable {ch['left_nullable']} → {ch['right_nullable']})"
                )
            lines.append("")

    if diff.fks_added:
        lines.append("## Foreign keys added")
        for fk in diff.fks_added:
            lines.append(
                f"- `{fk['from_table']}.{fk['from_column']}` → "
                f"`{fk['to_table']}.{fk['to_column']}`"
            )
        lines.append("")

    if diff.fks_removed:
        lines.append("## Foreign keys removed")
        for fk in diff.fks_removed:
            lines.append(
                f"- `{fk['from_table']}.{fk['from_column']}` → "
                f"`{fk['to_table']}.{fk['to_column']}`"
            )
        lines.append("")

    if diff.warnings:
        lines.append("## Warnings")
        for warning in diff.warnings:
            lines.append(f"- {warning}")
        lines.append("")

    return "\n".join(lines)


def diff_to_json(diff: SchemaDiff) -> str:
    payload: dict[str, Any] = {
        "has_changes": diff.has_changes,
        "tables_added": diff.tables_added,
        "tables_removed": diff.tables_removed,
        "columns_added": diff.columns_added,
        "columns_removed": diff.columns_removed,
        "columns_changed": diff.columns_changed,
        "fks_added": diff.fks_added,
        "fks_removed": diff.fks_removed,
        "warnings": diff.warnings,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
