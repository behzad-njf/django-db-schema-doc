# django-db-schema-doc

[![PyPI version](https://img.shields.io/pypi/v/django-db-schema-doc.svg)](https://pypi.org/project/django-db-schema-doc/)
[![Python versions](https://img.shields.io/pypi/pyversions/django-db-schema-doc.svg)](https://pypi.org/project/django-db-schema-doc/)
[![ERD explorer](https://img.shields.io/badge/demo-schema%20explorer-2563eb)](https://behzad-njf.github.io/django-db-schema-doc/)

**Schema intelligence for Django** — Markdown docs, JSON/DBML export, optional diff, and an interactive **React Flow** ERD from your live database.

**Live ERD explorer:** [behzad-njf.github.io/django-db-schema-doc](https://behzad-njf.github.io/django-db-schema-doc/) — open in the browser, upload `graph.json` from `python manage.py generate_erd`.

Supports **PostgreSQL**, **MySQL/MariaDB**, **Microsoft SQL Server**, **SQLite**, **Oracle**, and other backends Django can introspect.

## Install

```bash
pip install django-db-schema-doc
```

## Setup

```python
INSTALLED_APPS = [
    # ...
    "db_schema_doc",
]
```

## Commands

### Markdown documentation

```bash
python manage.py generate_database_doc
python manage.py generate_database_doc -o docs/schema.md --to-stdout
python manage.py generate_database_doc --with-row-counts --project-hints "Notes for AI agents."
```

When Django models use `db_table` matching the database, the doc also merges **model docstrings**, **verbose names**, and field **help text** (disable with `--no-model-metadata`). **Rule-based business context** (domain, FK roles, hub/junction heuristics, column hints) is added by default (`--no-business-descriptions` to skip).

### JSON snapshot (CI, diff, agents)

```bash
python manage.py export_schema_json -o schema.json
```

Stable format with `"schema_version": 1` — tables, columns, foreign keys, indexes, optional `django_model` / field labels, connection metadata (no passwords).

### AI / RAG export

```bash
python manage.py export_ai_schema -o ai_schema.json
python manage.py export_ai_schema --project-name "My Shop" --to-stdout
python manage.py export_ai_schema --no-fk-chunks   # table + overview chunks only
```

Produces `documents[]` with embeddable `content` per table (and optional per foreign key), plus `metadata` for filtering — suitable for vector DBs and agent context pipelines.

### Schema search (CLI + ERD)

```bash
python manage.py search_schema customer email
python manage.py search_schema order status --format json
python manage.py search_schema product --from-json schema.json
```

Matches table/column names, Django labels, business descriptions, and FK targets (light synonyms: e.g. `fk` → foreign key, `user` → customer). The ERD explorer search box uses the same idea on loaded `graph.json`.

### SQL / ORM query examples

```bash
python manage.py export_schema_examples -o schema_examples.json
```

Auto-generated per table when you run any schema command (disable with `--no-query-examples`): sample **SQL** (`SELECT`, `JOIN`, filters) and **Django ORM** snippets (`select_related`, `prefetch_related`, etc.). Shown in `DATABASE.md`, JSON exports, and the ERD table detail panel after `generate_erd`.

### DBML export

```bash
python manage.py export_dbml -o schema.dbml
```

Import into [dbdiagram.io](https://dbdiagram.io), [dbdocs.io](https://dbdocs.io), etc.

### Schema diff (optional)

```bash
python manage.py export_schema_json -o before.json   # baseline
# ... migrate ...
python manage.py export_schema_json -o after.json
python manage.py schema_diff before.json after.json -o SCHEMA_DIFF.md
```

### Interactive ERD (React Flow)

```bash
c
```

**Online:** use the [live explorer](https://behzad-njf.github.io/django-db-schema-doc/) (no install). **Offline:** open `schema-erd/index.html` from `generate_erd`. Double-click a table for details; Esc to clear focus / close panel.

The PyPI package includes pre-built UI assets. Contributors rebuilding the UI:

```bash
cd db_schema_doc/frontend && npm install && npm run build
```

## What Markdown includes

- Connection metadata (engine, vendor, database — no passwords)
- Tables grouped by name prefix / domain
- Hub tables (most referenced by FKs)
- TOC, FK index, per-table columns, PKs, indexes, incoming/outgoing FKs
- ON DELETE / ON UPDATE on PostgreSQL, MySQL, SQL Server when available

## Requirements

- Python 3.10+
- Django 4.2+
- Database driver for your project

## Development

Contributor roadmap and phase notes are maintained locally (not in the public repo).

```bash
git clone https://github.com/behzad-njf/django-db-schema-doc.git
cd django-db-schema-doc
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cd db_schema_doc/frontend && npm install && npm run build
cd ../../ && pytest
```

Demo project: [`examples/demo_project/`](examples/demo_project/).

## GitHub Pages (ERD website)

The interactive ERD is published on push to `main`/`master` via [`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml).

**One-time setup** on GitHub:

1. **Settings → Pages → Build and deployment**
2. **Source:** GitHub Actions (not “Deploy from a branch”)

After the workflow runs, the site is at:

**https://behzad-njf.github.io/django-db-schema-doc/**

Local production build (same as CI):

```bash
cd db_schema_doc/frontend
VITE_BASE_PATH=/django-db-schema-doc/ npm run build
```

## License

MIT — see [LICENSE](LICENSE).
