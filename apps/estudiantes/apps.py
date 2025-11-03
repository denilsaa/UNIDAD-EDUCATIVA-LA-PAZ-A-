from django.apps import AppConfig

class EstudiantesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.estudiantes"

    def ready(self):
        # Si ya tenías otras señales, déjalas
        try:
            from . import signals  # opcional, si existe
        except Exception:
            pass

        try:
            from .views import signals_citaciones  # noqa: F401
        except Exception:
            # Evita romper en migraciones tempranas
            pass
