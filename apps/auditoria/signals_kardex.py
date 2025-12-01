# apps/auditoria/signals_kardex.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.estudiantes.models.kardex_registro import KardexRegistro
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


def _repr_item(item):
    if not item:
        return ""
    area = item.get_area_display() if hasattr(item, "get_area_display") else item.area
    sentido = item.get_sentido_display() if hasattr(item, "get_sentido_display") else item.sentido
    return f"{area} · {item.descripcion} ({sentido})"


@receiver(post_save, sender=KardexRegistro)
def log_kardex_save(sender, instance: KardexRegistro, created, **kwargs):
    """
    Registra creación / edición de un registro de kárdex.
    """
    user, ip, ua = _get_user_ip_ua()
    est = instance.estudiante
    est_repr = _repr_estudiante(est)
    item = instance.kardex_item
    item_repr = _repr_item(item)

    fecha_txt = instance.fecha.strftime("%d/%m/%Y") if instance.fecha else "sin fecha"

    if created:
        accion = StudentLog.Accion.CREAR
        pref = "Registró un ítem de kárdex"
    else:
        accion = StudentLog.Accion.EDITAR
        pref = "Actualizó un ítem de kárdex"

    desc = (
        f"{pref} para el estudiante {est_repr} "
        f"en la fecha {fecha_txt}: {item_repr}. "
    )

    if instance.observacion:
        desc += f"Observación: {instance.observacion[:200]}"

    StudentLog.objects.create(
        usuario=user,
        estudiante=est,
        estudiante_nombre=est_repr,
        accion=accion,
        descripcion=desc,
        ip=ip,
        user_agent=ua,
    )


@receiver(post_delete, sender=KardexRegistro)
def log_kardex_delete(sender, instance: KardexRegistro, **kwargs):
    """
    Registra eliminación de un registro de kárdex.
    """
    user, ip, ua = _get_user_ip_ua()
    est = instance.estudiante
    est_repr = _repr_estudiante(est)

    item = instance.kardex_item
    item_repr = _repr_item(item)
    fecha_txt = instance.fecha.strftime("%d/%m/%Y") if instance.fecha else "sin fecha"

    desc = (
        f"Eliminó un registro de kárdex del estudiante {est_repr} "
        f"({item_repr}) correspondiente a la fecha {fecha_txt}."
    )

    if instance.observacion:
        desc += f" Observación previa: {instance.observacion[:200]}"

    StudentLog.objects.create(
        usuario=user,
        estudiante=est,
        estudiante_nombre=est_repr,
        accion=StudentLog.Accion.ELIMINAR,
        descripcion=desc,
        ip=ip,
        user_agent=ua,
    )
