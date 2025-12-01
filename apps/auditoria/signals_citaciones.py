# apps/auditoria/signals_citaciones.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.citaciones.models.citacion import Citacion
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


def _repr_estado(cit: Citacion):
    if hasattr(cit, "get_estado_display"):
        return cit.get_estado_display()
    return cit.estado


@receiver(post_save, sender=Citacion)
def log_citacion_save(sender, instance: Citacion, created, **kwargs):
    """
    Registra creación / actualización de una citación.
    """
    user, ip, ua = _get_user_ip_ua()
    est = instance.estudiante
    est_repr = _repr_estudiante(est)
    estado_txt = _repr_estado(instance)

    fecha_txt = (
        instance.fecha_citacion.strftime("%d/%m/%Y")
        if getattr(instance, "fecha_citacion", None)
        else "sin fecha"
    )
    hora_txt = (
        instance.hora_citacion.strftime("%H:%M")
        if getattr(instance, "hora_citacion", None)
        else "sin hora"
    )

    if created:
        accion = StudentLog.Accion.CREAR
        pref = "Creó una citación"
    else:
        accion = StudentLog.Accion.EDITAR
        pref = "Actualizó una citación"

    desc = (
        f"{pref} para el estudiante {est_repr}. "
        f"Estado: {estado_txt}. "
        f"Fecha/hora de citación: {fecha_txt} {hora_txt}. "
    )

    if getattr(instance, "motivo_resumen", None):
        desc += f"Motivo: {instance.motivo_resumen[:200]}"

    StudentLog.objects.create(
        usuario=user,
        estudiante=est,
        estudiante_nombre=est_repr,
        accion=accion,
        descripcion=desc,
        ip=ip,
        user_agent=ua,
    )


@receiver(post_delete, sender=Citacion)
def log_citacion_delete(sender, instance: Citacion, **kwargs):
    """
    Registra eliminación de una citación.
    """
    user, ip, ua = _get_user_ip_ua()
    est = instance.estudiante
    est_repr = _repr_estudiante(est)
    estado_txt = _repr_estado(instance)

    desc = (
        f"Eliminó una citación del estudiante {est_repr}. "
        f"Último estado: {estado_txt}. "
    )

    if getattr(instance, "motivo_resumen", None):
        desc += f"Motivo: {instance.motivo_resumen[:200]}"

    StudentLog.objects.create(
        usuario=user,
        estudiante=est,
        estudiante_nombre=est_repr,
        accion=StudentLog.Accion.ELIMINAR,
        descripcion=desc,
        ip=ip,
        user_agent=ua,
    )
