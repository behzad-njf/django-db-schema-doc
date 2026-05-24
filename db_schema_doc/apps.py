from django.apps import AppConfig


class DbSchemaDocConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "db_schema_doc"
    verbose_name = "Database schema documentation"
