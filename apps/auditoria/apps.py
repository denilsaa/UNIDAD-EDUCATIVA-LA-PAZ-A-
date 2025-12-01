# apps/auditoria/apps.py
from django.apps import AppConfig


class AuditoriaConfig(AppConfig):
  default_auto_field = "django.db.models.BigAutoField"
  name = "apps.auditoria"
  label = "auditoria"

  def ready(self):
    # Auditoría de estudiantes (ya la tenías)
    from . import signals_estudiantes  # noqa

    # 👇 NUEVO: auditoría de otros módulos del estudiante
    from . import signals_asistencia   # noqa
    from . import signals_kardex       # noqa
    from . import signals_citaciones   # noqa
