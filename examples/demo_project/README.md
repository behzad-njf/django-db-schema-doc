# Demo project

Small Django shop app for developing and testing `django-db-schema-doc`.

## Setup (from repository root)

```bash
pip install -e ".[dev]"
cd db_schema_doc/frontend && npm install && npm run build
cd ../../examples/demo_project
python manage.py migrate
```

## Generate outputs

```bash
python manage.py generate_database_doc -o DATABASE.md
python manage.py export_schema_json -o schema.json
python manage.py export_dbml -o schema.dbml
python manage.py generate_erd -o schema-erd
python manage.py generate_database_doc --to-stdout
```

Open `schema-erd/index.html` for the interactive ERD.

## Models

`shop_customer`, `shop_product`, `shop_order`, `shop_orderitem` — foreign keys for ERD and diff testing.
