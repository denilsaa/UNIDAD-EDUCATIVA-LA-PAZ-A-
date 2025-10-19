from django.apps import AppConfig

class EstudiantesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.estudiantes"

    def ready(self):
        from . import signals  
