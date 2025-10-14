from django.apps import AppConfig

class CitacionesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.citaciones"

    def ready(self):
        # registra señales (recalcular puntaje/severidad)
        from .models import signals  # noqa
