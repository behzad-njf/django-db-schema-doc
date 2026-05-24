# django-db-schema-doc

[![PyPI version](https://img.shields.io/pypi/v/django-db-schema-doc.svg)](https://pypi.org/project/django-db-schema-doc/)
[![Python versions](https://img.shields.io/pypi/pyversions/django-db-schema-doc.svg)](https://pypi.org/project/django-db-schema-doc/)

Generate **DATABASE.md** — full schema documentation for developers and LLM/AI agents — from any database configured in your Django project's `DATABASES`.

Supports **PostgreSQL**, **MySQL/MariaDB**, **Microsoft SQL Server**, **SQLite**, **Oracle**, and other backends Django can introspect.

## Install

```bash
pip install django-db-schema-doc
```

## Setup

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "db_schema_doc",
]
```

## Usage

```bash
python manage.py generate_database_doc
```

Writes `DATABASE.md` in your project `BASE_DIR` by default.

### Common options

```bash
python manage.py generate_database_doc -o docs/schema.md
python manage.py generate_database_doc --with-row-counts
python manage.py generate_database_doc --database reporting
python manage.py generate_database_doc --project-hints "See accounts_childuserrelation for parent-child links."
```

Run `python manage.py generate_database_doc --help` for all options.

## What is generated

- Connection metadata (engine, vendor, database — no passwords)
- Tables grouped by name prefix (`app_model` style)
- Hub tables (most referenced by foreign keys)
- Table of contents with anchors
- Foreign key index
- Per table: columns, types, PKs, indexes, incoming/outgoing FKs

On PostgreSQL, MySQL, and SQL Server, foreign keys include `ON DELETE` / `ON UPDATE` rules when available.

## Requirements

- Python 3.10+
- Django 4.2+
- Your project's database driver (e.g. `psycopg`, `mysqlclient`, `mssql-django`)

## License

MIT — see [LICENSE](LICENSE).
