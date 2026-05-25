"""
Natural-language-ish schema search (keyword + synonym matching, no LLM).

Scores matches across table names, domains, columns, Django metadata,
business descriptions, and foreign-key relationships.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .collector import ColumnInfo, DatabaseSchema, ForeignKeyInfo, TableInfo
from .writer import infer_domain

# Extra terms to try when a token appears in the query (light NL helpers).
TOKEN_EXPANSIONS: dict[str, list[str]] = {
    "fk": ["foreign", "key", "reference", "references"],
    "foreign": ["fk", "reference"],
    "pk": ["primary", "key"],
    "primary": ["pk"],
    "user": ["customer", "auth", "account"],
    "customer": ["client", "buyer", "user"],
    "order": ["purchase", "sale"],
    "product": ["item", "sku", "catalog"],
    "email": ["mail"],
    "money": ["price", "amount", "cost", "fee", "total"],
    "status": ["state", "phase"],
    "delete": ["removed", "soft"],
}

FK_HINT_TOKENS = frozenset(
    {"fk", "foreign", "reference", "references", "join", "relationship"}
)
PK_HINT_TOKENS = frozenset({"pk", "primary"})

STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "is",
        "are",
        "in",
        "on",
        "for",
        "to",
        "of",
        "with",
        "what",
        "which",
        "where",
        "how",
        "show",
        "find",
        "list",
        "table",
        "tables",
        "column",
        "columns",
        "key",
    }
)

FIELD_WEIGHTS: dict[str, float] = {
    "table_name": 100.0,
    "domain": 40.0,
    "django_model": 70.0,
    "model_doc": 55.0,
    "business": 50.0,
    "business_hint": 35.0,
    "column_name": 80.0,
    "django_field": 65.0,
    "column_label": 45.0,
    "column_help": 40.0,
    "column_type": 25.0,
    "fk_target": 60.0,
    "fk_column": 45.0,
}


@dataclass
class SchemaSearchHit:
    kind: str
    score: float
    table: str
    field: str
    snippet: str
    column: str | None = None

    def to_dict(self) -> dict:
        payload = {
            "kind": self.kind,
            "score": round(self.score, 2),
            "table": self.table,
            "field": self.field,
            "snippet": self.snippet,
        }
        if self.column:
            payload["column"] = self.column
        return payload


@dataclass
class _Searchable:
    kind: str
    table: str
    field: str
    text: str
    snippet: str
    column: str | None = None


def tokenize_query(query: str) -> list[str]:
    raw = re.findall(r"[a-z0-9_]+", query.lower())
    return [t for t in raw if t not in STOPWORDS and len(t) > 1]


def parse_query(query: str) -> tuple[list[str], bool, bool]:
    """Return (content_tokens, wants_fk_hits, wants_pk_hits)."""
    tokens = tokenize_query(query)
    wants_fk = any(t in FK_HINT_TOKENS for t in tokens)
    wants_pk = any(t in PK_HINT_TOKENS for t in tokens)
    content = [t for t in tokens if t not in FK_HINT_TOKENS and t not in PK_HINT_TOKENS]
    return content, wants_fk, wants_pk


def expand_token(token: str) -> list[str]:
    terms = {token}
    for extra in TOKEN_EXPANSIONS.get(token, []):
        terms.add(extra)
    for key, extras in TOKEN_EXPANSIONS.items():
        if token in extras:
            terms.add(key)
            terms.update(extras)
    return list(terms)


def search_schema(
    schema: DatabaseSchema,
    query: str,
    *,
    limit: int = 25,
    min_score: float = 1.0,
) -> list[SchemaSearchHit]:
    content_tokens, wants_fk, wants_pk = parse_query(query)
    if not content_tokens and not wants_fk and not wants_pk:
        return []

    records: list[_Searchable] = []
    for table in schema.tables:
        records.extend(_records_for_table(table))

    scored: list[SchemaSearchHit] = []
    for record in records:
        score = _score_record(record, content_tokens, wants_fk, wants_pk)
        if score >= min_score:
            scored.append(
                SchemaSearchHit(
                    kind=record.kind,
                    score=score,
                    table=record.table,
                    column=record.column,
                    field=record.field,
                    snippet=record.snippet,
                )
            )

    scored.sort(key=lambda h: (-h.score, h.table, h.column or "", h.kind))
    return scored[:limit]


def format_hits_text(hits: list[SchemaSearchHit], *, query: str) -> str:
    if not hits:
        return f"No matches for {query!r}.\n"
    lines = [f"Search: {query!r} ({len(hits)} result(s))", ""]
    for hit in hits:
        col = f".{hit.column}" if hit.column else ""
        lines.append(
            f"[{hit.score:.0f}] {hit.table}{col} ({hit.kind}) — {hit.snippet}"
        )
    return "\n".join(lines) + "\n"


def _records_for_table(table: TableInfo) -> list[_Searchable]:
    domain = infer_domain(table.name)
    records: list[_Searchable] = [
        _Searchable(
            kind="table",
            table=table.name,
            field="table_name",
            text=_join(table.name, domain),
            snippet=f"Table `{table.name}`",
        ),
        _Searchable(
            kind="table",
            table=table.name,
            field="domain",
            text=_join(domain, table.name),
            snippet=f"Domain `{domain}`",
        ),
    ]

    if table.django_model is not None:
        dm = table.django_model
        path = f"{dm.app_label}.{dm.model_name}"
        records.append(
            _Searchable(
                kind="table",
                table=table.name,
                field="django_model",
                text=_join(path, dm.verbose_name, dm.verbose_name_plural),
                snippet=f"Django model `{path}`",
            )
        )
        if dm.doc:
            records.append(
                _Searchable(
                    kind="table",
                    table=table.name,
                    field="model_doc",
                    text=dm.doc.lower(),
                    snippet=_truncate(dm.doc),
                )
            )

    if table.business is not None:
        if table.business.description:
            records.append(
                _Searchable(
                    kind="business",
                    table=table.name,
                    field="business",
                    text=table.business.description.lower(),
                    snippet=_truncate(table.business.description),
                )
            )
        for hint in table.business.hints:
            records.append(
                _Searchable(
                    kind="business",
                    table=table.name,
                    field="business_hint",
                    text=hint.lower(),
                    snippet=_truncate(hint),
                )
            )

    for col in table.columns:
        records.extend(_records_for_column(table.name, col))

    for fk in table.outgoing_fks:
        records.append(_record_for_fk(table.name, fk))

    return records


def _records_for_column(table_name: str, col: ColumnInfo) -> list[_Searchable]:
    base = _join(
        col.name,
        col.django_field,
        col.verbose_name,
        col.help_text,
        col.type_display,
    )
    records = [
        _Searchable(
            kind="column",
            table=table_name,
            column=col.name,
            field="column_name",
            text=base,
            snippet=f"Column `{col.name}` ({col.type_display})",
        ),
    ]
    if col.django_field:
        records.append(
            _Searchable(
                kind="column",
                table=table_name,
                column=col.name,
                field="django_field",
                text=_join(col.django_field, col.name),
                snippet=f"Django field `{col.django_field}`",
            )
        )
    if col.verbose_name:
        records.append(
            _Searchable(
                kind="column",
                table=table_name,
                column=col.name,
                field="column_label",
                text=col.verbose_name.lower(),
                snippet=col.verbose_name,
            )
        )
    if col.help_text:
        records.append(
            _Searchable(
                kind="column",
                table=table_name,
                column=col.name,
                field="column_help",
                text=col.help_text.lower(),
                snippet=_truncate(col.help_text),
            )
        )
    return records


def _record_for_fk(table_name: str, fk: ForeignKeyInfo) -> _Searchable:
    text = _join(
        fk.from_column,
        fk.to_table,
        fk.to_column,
        fk.on_delete,
        fk.on_update,
    )
    return _Searchable(
        kind="foreign_key",
        table=table_name,
        field="fk_target",
        text=text,
        snippet=(
            f"FK `{fk.from_column}` → `{fk.to_table}.{fk.to_column}`"
        ),
    )


def _score_record(
    record: _Searchable,
    content_tokens: list[str],
    wants_fk: bool,
    wants_pk: bool,
) -> float:
    if wants_fk and record.kind != "foreign_key":
        return 0.0
    if wants_pk and record.kind != "column":
        return 0.0

    text = record.text.lower()
    if not text and content_tokens:
        return 0.0

    total = 0.0
    if wants_fk and record.kind == "foreign_key":
        total += 25.0
    if wants_pk and record.field == "column_name":
        col_pk = "primary" in text or record.snippet.lower().find("pk") >= 0
        # PK columns flagged via is_primary_key in snippet path — check name only
        total += 15.0

    for token in content_tokens:
        variants = expand_token(token)
        best = 0.0
        for variant in variants:
            best = max(best, _token_score(text, variant, FIELD_WEIGHTS[record.field]))
        if best <= 0:
            return 0.0
        total += best

    if not content_tokens and (wants_fk or wants_pk):
        return total or 1.0
    return total


def _token_score(text: str, token: str, weight: float) -> float:
    if token not in text:
        return 0.0
    if re.search(rf"\b{re.escape(token)}\b", text):
        return weight
    return weight * 0.65


def _join(*parts: str) -> str:
    return " ".join(p.lower() for p in parts if p).strip()


def _truncate(text: str, max_len: int = 120) -> str:
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
