from django.apps import AppConfig

class EstudiantesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.estudiantes"

    def ready(self):
        # (opcional) si tienes otras señales
        try:
            import apps.estudiantes.signals  # noqa
        except Exception:
            pass

        # 👇 IMPORTANTE: registra el receiver que crea citaciones
        try:
            import apps.estudiantes.signals_citaciones  # noqa
        except Exception:
            pass
