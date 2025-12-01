# apps/auditoria/signals_asistencia.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.estudiantes.models.asistencia import Asistencia
from .models import StudentLog
from .utils import get_request, get_ip_ua_from_request


def _get_user_ip_ua():
    request = get_request()
    user = getattr(request, "user", None) if request else None
    ip, ua = get_ip_ua_from_request(request)
    if not getattr(user, "is_authenticated", False):
        user = None
    return user, ip, ua


def _repr_estudiante(est):
    if not est:
        return ""
    return f"{est.apellidos}, {est.nombres}"


@receiver(post_save, sender=Asistencia)
def log_asistencia_save(sender, instance: Asistencia, created, **kwargs):
    """
    Registra cuando se crea o actualiza una asistencia.
    """
    user, ip, ua = _get_user_ip_ua()
    est = instance.estudiante
    est_repr = _repr_estudiante(est)

    fecha_txt = instance.fecha.strftime("%d/%m/%Y") if instance.fecha else "sin fecha"
    estado_txt = instance.get_estado_display() if hasattr(instance, "get_estado_display") else instance.estado

    if created:
        accion = StudentLog.Accion.CREAR
        desc = (
            f"Registró asistencia ({estado_txt}) para el estudiante {est_repr} "
            f"en la fecha {fecha_txt}."
        )
    else:
        accion = StudentLog.Accion.EDITAR
        desc = (
            f"Actualizó la asistencia del estudiante {est_repr} "
            f"para la fecha {fecha_txt}. Estado actual: {estado_txt}."
        )

    StudentLog.objects.create(
        usuario=user,
        estudiante=est,
        estudiante_nombre=est_repr,
        accion=accion,
        descripcion=desc,
        ip=ip,
        user_agent=ua,
    )


@receiver(post_delete, sender=Asistencia)
def log_asistencia_delete(sender, instance: Asistencia, **kwargs):
    """
    Registra cuando se elimina un registro de asistencia.
    """
    user, ip, ua = _get_user_ip_ua()
    est = instance.estudiante
    est_repr = _repr_estudiante(est)

    fecha_txt = instance.fecha.strftime("%d/%m/%Y") if instance.fecha else "sin fecha"

    desc = (
        f"Eliminó un registro de asistencia del estudiante {est_repr} "
        f"correspondiente a la fecha {fecha_txt}."
    )

    StudentLog.objects.create(
        usuario=user,
        estudiante=est,
        estudiante_nombre=est_repr,
        accion=StudentLog.Accion.ELIMINAR,
        descripcion=desc,
        ip=ip,
        user_agent=ua,
    )
