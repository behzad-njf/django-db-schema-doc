"""
Collect database schema metadata using Django's introspection API.

Works with any database backend Django supports (PostgreSQL, MySQL/MariaDB,
Microsoft SQL Server, Oracle, SQLite, etc.). Optional INFORMATION_SCHEMA
queries enrich foreign-key ON DELETE / ON UPDATE rules when available.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from django.db import connections


@dataclass
class ColumnInfo:
    name: str
    type_display: str
    nullable: bool
    default: str | None
    ordinal: int
    is_primary_key: bool = False


@dataclass
class ForeignKeyInfo:
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    constraint_name: str = ""
    on_delete: str = ""
    on_update: str = ""


@dataclass
class IndexInfo:
    name: str
    columns: list[str]
    unique: bool = False


@dataclass
class TableInfo:
    name: str
    schema: str = "dbo"
    columns: list[ColumnInfo] = field(default_factory=list)
    primary_key: list[str] = field(default_factory=list)
    outgoing_fks: list[ForeignKeyInfo] = field(default_factory=list)
    incoming_fks: list[ForeignKeyInfo] = field(default_factory=list)
    indexes: list[IndexInfo] = field(default_factory=list)
    row_count: int | None = None


@dataclass
class DatabaseSchema:
    vendor: str
    database_name: str
    host: str
    port: str
    engine: str
    tables: list[TableInfo] = field(default_factory=list)

    @property
    def fk_count(self) -> int:
        return sum(len(t.outgoing_fks) for t in self.tables)

    @property
    def column_count(self) -> int:
        return sum(len(t.columns) for t in self.tables)


class SchemaCollector:
    """Introspect a Django database connection and build a DatabaseSchema."""

    def __init__(self, database: str = "default", include_views: bool = False):
        self.database = database
        self.include_views = include_views
        self.connection = connections[database]

    def collect(self, row_counts: bool = False) -> DatabaseSchema:
        introspection = self.connection.introspection
        settings_dict = self.connection.settings_dict

        with self.connection.cursor() as cursor:
            db_name = self._database_name(cursor)
            table_names = introspection.table_names(
                cursor, include_views=self.include_views
            )
            table_names = sorted(set(table_names))

            fk_rules = self._fetch_fk_rules(cursor)
            tables: list[TableInfo] = []

            for table_name in table_names:
                table = self._collect_table(
                    cursor, introspection, table_name, fk_rules
                )
                if row_counts:
                    table.row_count = self._row_count(cursor, table_name)
                tables.append(table)

        incoming = self._build_incoming_fks(tables)
        for table in tables:
            table.incoming_fks = incoming.get(table.name, [])

        return DatabaseSchema(
            vendor=self.connection.vendor,
            database_name=db_name,
            host=str(settings_dict.get("HOST", "")),
            port=str(settings_dict.get("PORT", "")),
            engine=str(settings_dict.get("ENGINE", "")),
            tables=tables,
        )

    def _database_name(self, cursor) -> str:
        try:
            if self.connection.vendor == "postgresql":
                cursor.execute("SELECT current_database()")
            elif self.connection.vendor == "mysql":
                cursor.execute("SELECT DATABASE()")
            elif self.connection.vendor == "microsoft":
                cursor.execute("SELECT DB_NAME()")
            elif self.connection.vendor == "sqlite":
                return str(self.connection.settings_dict.get("NAME", "sqlite"))
            else:
                cursor.execute("SELECT 1")
                return str(self.connection.settings_dict.get("NAME", ""))
            return str(cursor.fetchone()[0])
        except Exception:
            return str(self.connection.settings_dict.get("NAME", "unknown"))

    def _collect_table(
        self, cursor, introspection, table_name: str, fk_rules: dict
    ) -> TableInfo:
        pk_columns = list(introspection.get_primary_key_columns(cursor, table_name))
        descriptions = introspection.get_table_description(cursor, table_name)

        columns: list[ColumnInfo] = []
        for ordinal, col in enumerate(descriptions, start=1):
            type_display = introspection.get_field_type(col.type_code, col)
            columns.append(
                ColumnInfo(
                    name=col.name,
                    type_display=type_display,
                    nullable=bool(col.null_ok),
                    default=self._format_default(col.default),
                    ordinal=ordinal,
                    is_primary_key=col.name in pk_columns,
                )
            )

        outgoing = self._collect_outgoing_fks(
            cursor, introspection, table_name, fk_rules
        )
        indexes = self._collect_indexes(introspection, cursor, table_name, pk_columns)

        return TableInfo(
            name=table_name,
            columns=columns,
            primary_key=pk_columns,
            outgoing_fks=outgoing,
            indexes=indexes,
        )

    def _collect_outgoing_fks(
        self, cursor, introspection, table_name: str, fk_rules: dict
    ) -> list[ForeignKeyInfo]:
        fks: list[ForeignKeyInfo] = []
        seen: set[tuple[str, str, str, str]] = set()

        try:
            key_columns = introspection.get_key_columns(cursor, table_name)
        except NotImplementedError:
            key_columns = []

        for from_col, to_table, to_col in key_columns:
            key = (table_name, from_col, to_table, to_col)
            if key in seen:
                continue
            seen.add(key)
            rules = fk_rules.get((table_name, from_col), {})
            fks.append(
                ForeignKeyInfo(
                    from_table=table_name,
                    from_column=from_col,
                    to_table=to_table,
                    to_column=to_col,
                    constraint_name=rules.get("constraint_name", ""),
                    on_delete=rules.get("on_delete", ""),
                    on_update=rules.get("on_update", ""),
                )
            )

        # Fallback: constraints API (some backends only expose FKs here)
        try:
            constraints = introspection.get_constraints(cursor, table_name)
        except NotImplementedError:
            constraints = {}

        for cname, info in constraints.items():
            fk = info.get("foreign_key")
            if not fk:
                continue
            to_table, to_col = fk
            for from_col in info.get("columns", []):
                key = (table_name, from_col, to_table, to_col)
                if key in seen:
                    continue
                seen.add(key)
                rules = fk_rules.get((table_name, from_col), {})
                fks.append(
                    ForeignKeyInfo(
                        from_table=table_name,
                        from_column=from_col,
                        to_table=to_table,
                        to_column=to_col,
                        constraint_name=cname,
                        on_delete=rules.get("on_delete", ""),
                        on_update=rules.get("on_update", ""),
                    )
                )

        return sorted(fks, key=lambda f: (f.from_column, f.to_table))

    def _collect_indexes(
        self, introspection, cursor, table_name: str, pk_columns: list[str]
    ) -> list[IndexInfo]:
        indexes: list[IndexInfo] = []
        try:
            constraints = introspection.get_constraints(cursor, table_name)
        except NotImplementedError:
            return indexes

        for name, info in constraints.items():
            if not info.get("index"):
                continue
            if info.get("primary_key"):
                continue
            cols = info.get("columns") or []
            if not cols:
                continue
            indexes.append(
                IndexInfo(
                    name=name,
                    columns=list(cols),
                    unique=bool(info.get("unique")),
                )
            )
        return sorted(indexes, key=lambda i: i.name)

    def _fetch_fk_rules(self, cursor) -> dict[tuple[str, str], dict[str, str]]:
        """Optional FK ON DELETE/UPDATE from INFORMATION_SCHEMA (where supported)."""
        vendor = self.connection.vendor
        if vendor == "microsoft":
            return self._fk_rules_mssql(cursor)
        if vendor == "postgresql":
            return self._fk_rules_postgresql(cursor)
        if vendor == "mysql":
            return self._fk_rules_mysql(cursor)
        return {}

    def _fk_rules_mssql(self, cursor) -> dict[tuple[str, str], dict[str, str]]:
        sql = """
            SELECT
                fk.TABLE_NAME,
                fk.COLUMN_NAME,
                rc.CONSTRAINT_NAME,
                rc.DELETE_RULE,
                rc.UPDATE_RULE
            FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE fk
              ON rc.CONSTRAINT_NAME = fk.CONSTRAINT_NAME
             AND rc.CONSTRAINT_SCHEMA = fk.CONSTRAINT_SCHEMA
        """
        try:
            cursor.execute(sql)
            rows = cursor.fetchall()
        except Exception:
            return {}
        result = {}
        for table, column, cname, on_delete, on_update in rows:
            result[(table, column)] = {
                "constraint_name": cname,
                "on_delete": on_delete or "",
                "on_update": on_update or "",
            }
        return result

    def _fk_rules_postgresql(self, cursor) -> dict[tuple[str, str], dict[str, str]]:
        sql = """
            SELECT
                tc.table_name,
                kcu.column_name,
                tc.constraint_name,
                rc.delete_rule,
                rc.update_rule
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            JOIN information_schema.referential_constraints rc
              ON tc.constraint_name = rc.constraint_name
             AND tc.table_schema = rc.constraint_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
        """
        try:
            cursor.execute(sql)
            rows = cursor.fetchall()
        except Exception:
            return {}
        result = {}
        for table, column, cname, on_delete, on_update in rows:
            result[(table, column)] = {
                "constraint_name": cname,
                "on_delete": on_delete or "",
                "on_update": on_update or "",
            }
        return result

    def _fk_rules_mysql(self, cursor) -> dict[tuple[str, str], dict[str, str]]:
        sql = """
            SELECT
                kcu.TABLE_NAME,
                kcu.COLUMN_NAME,
                kcu.CONSTRAINT_NAME,
                rc.DELETE_RULE,
                rc.UPDATE_RULE
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
            JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
              ON kcu.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
             AND kcu.CONSTRAINT_SCHEMA = rc.CONSTRAINT_SCHEMA
            WHERE kcu.REFERENCED_TABLE_NAME IS NOT NULL
              AND kcu.TABLE_SCHEMA = DATABASE()
        """
        try:
            cursor.execute(sql)
            rows = cursor.fetchall()
        except Exception:
            return {}
        result = {}
        for table, column, cname, on_delete, on_update in rows:
            result[(table, column)] = {
                "constraint_name": cname,
                "on_delete": on_delete or "",
                "on_update": on_update or "",
            }
        return result

    def _build_incoming_fks(
        self, tables: list[TableInfo]
    ) -> dict[str, list[ForeignKeyInfo]]:
        incoming: dict[str, list[ForeignKeyInfo]] = defaultdict(list)
        for table in tables:
            for fk in table.outgoing_fks:
                incoming[fk.to_table].append(fk)
        for refs in incoming.values():
            refs.sort(key=lambda f: (f.from_table, f.from_column))
        return dict(incoming)

    def _row_count(self, cursor, table_name: str) -> int | None:
        qn = self.connection.ops.quote_name(table_name)
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {qn}")
            return int(cursor.fetchone()[0])
        except Exception:
            return None

    @staticmethod
    def _format_default(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if len(text) > 80:
            return text[:77] + "..."
        return text
