"""Compare two JSON schema snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SchemaDiff:
    tables_added: list[str] = field(default_factory=list)
    tables_removed: list[str] = field(default_factory=list)
    columns_added: dict[str, list[str]] = field(default_factory=dict)
    columns_removed: dict[str, list[str]] = field(default_factory=dict)
    columns_changed: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    fks_added: list[dict[str, str]] = field(default_factory=list)
    fks_removed: list[dict[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(
            self.tables_added
            or self.tables_removed
            or self.columns_added
            or self.columns_removed
            or self.columns_changed
            or self.fks_added
            or self.fks_removed
        )


def compare_schema_dicts(left: dict[str, Any], right: dict[str, Any]) -> SchemaDiff:
    diff = SchemaDiff()
    left_tables = {t["name"]: t for t in left.get("tables", [])}
    right_tables = {t["name"]: t for t in right.get("tables", [])}

    diff.tables_added = sorted(set(right_tables) - set(left_tables))
    diff.tables_removed = sorted(set(left_tables) - set(right_tables))

    for name in sorted(set(left_tables) & set(right_tables)):
        lt, rt = left_tables[name], right_tables[name]
        _diff_columns(diff, name, lt, rt)
        _diff_fks(diff, lt, rt)

    for removed, added in _possible_renames(diff.tables_removed, diff.tables_added):
        diff.warnings.append(
            f"Possible rename: `{removed}` → `{added}` (verify migrations)."
        )

    return diff


def _diff_columns(diff: SchemaDiff, table: str, left: dict, right: dict) -> None:
    left_cols = {c["name"]: c for c in left.get("columns", [])}
    right_cols = {c["name"]: c for c in right.get("columns", [])}

    added = sorted(set(right_cols) - set(left_cols))
    removed = sorted(set(left_cols) - set(right_cols))
    if added:
        diff.columns_added[table] = added
    if removed:
        diff.columns_removed[table] = removed

    changed: list[dict[str, Any]] = []
    for name in sorted(set(left_cols) & set(right_cols)):
        lc, rc = left_cols[name], right_cols[name]
        if lc.get("type_display") != rc.get("type_display") or lc.get("nullable") != rc.get(
            "nullable"
        ):
            changed.append(
                {
                    "column": name,
                    "left_type": lc.get("type_display"),
                    "right_type": rc.get("type_display"),
                    "left_nullable": lc.get("nullable"),
                    "right_nullable": rc.get("nullable"),
                }
            )
    if changed:
        diff.columns_changed[table] = changed


def _fk_key(fk: dict) -> tuple[str, str, str, str]:
    return (
        fk.get("from_table", ""),
        fk.get("from_column", ""),
        fk.get("to_table", ""),
        fk.get("to_column", ""),
    )


def _diff_fks(diff: SchemaDiff, left: dict, right: dict) -> None:
    left_fks = {_fk_key(fk): fk for fk in left.get("outgoing_fks", [])}
    right_fks = {_fk_key(fk): fk for fk in right.get("outgoing_fks", [])}
    for key in sorted(set(right_fks) - set(left_fks)):
        diff.fks_added.append(_fk_summary(right_fks[key]))
    for key in sorted(set(left_fks) - set(right_fks)):
        diff.fks_removed.append(_fk_summary(left_fks[key]))


def _fk_summary(fk: dict) -> dict[str, str]:
    return {
        "from_table": fk.get("from_table", ""),
        "from_column": fk.get("from_column", ""),
        "to_table": fk.get("to_table", ""),
        "to_column": fk.get("to_column", ""),
    }


def _possible_renames(removed: list[str], added: list[str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for r in removed:
        prefix = r.split("_")[0] if "_" in r else r
        for a in added:
            if a.split("_")[0] == prefix and r != a:
                pairs.append((r, a))
                break
    return pairs[:5]
