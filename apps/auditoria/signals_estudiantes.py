from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.estudiantes.models import Estudiante
from .models import StudentLog
from .utils import get_request, get_ip_ua_from_request


@receiver(post_save, sender=Estudiante)
def log_estudiante_save(sender, instance, created, **kwargs):
  """
  Registra creación y modificación de estudiantes.
  """
  request = get_request()
  ip, ua = get_ip_ua_from_request(request)
  user = getattr(request, "user", None) if request else None
  if user is not None and not getattr(user, "is_authenticated", False):
    user = None

  if created:
    accion = StudentLog.Accion.CREAR
    desc = f"Creó al estudiante {instance}"
  else:
    accion = StudentLog.Accion.EDITAR
    desc = f"Modificó al estudiante {instance}"

  StudentLog.objects.create(
    usuario=user,
    estudiante=instance,
    accion=accion,
    descripcion=desc,
    ip=ip,
    user_agent=ua,
  )


@receiver(post_delete, sender=Estudiante)
def log_estudiante_delete(sender, instance, **kwargs):
  """
  Registra eliminación de estudiantes.
  """
  request = get_request()
  ip, ua = get_ip_ua_from_request(request)
  user = getattr(request, "user", None) if request else None
  if user is not None and not getattr(user, "is_authenticated", False):
    user = None

  StudentLog.objects.create(
    usuario=user,
    estudiante=None,  # ya se eliminó
    accion=StudentLog.Accion.ELIMINAR,
    descripcion=f"Eliminó al estudiante {instance}",
    ip=ip,
    user_agent=ua,
  )
