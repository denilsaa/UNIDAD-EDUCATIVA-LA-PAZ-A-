from django.apps import AppConfig


class AuditoriaConfig(AppConfig):
  default_auto_field = "django.db.models.BigAutoField"
  name = "apps.auditoria"   # IMPORTANTE: con 'apps.'
  label = "auditoria"

  def ready(self):
    # Cargamos señales relacionadas con estudiantes
    from . import signals_estudiantes  # noqa
