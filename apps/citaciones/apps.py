# apps/citaciones/apps.py
from django.apps import AppConfig

class CitacionesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.citaciones"

    def ready(self):
        import apps.citaciones.signals  # noqa
