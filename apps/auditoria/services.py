from typing import Optional
from django.http import HttpRequest

from .models import StudentLog, Estudiante


def _get_client_ip(request: HttpRequest) -> Optional[str]:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        # Si hay proxy, tomamos el primero
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def registrar_accion_estudiante(
    request: HttpRequest,
    accion: str,
    estudiante: Optional[Estudiante] = None,
    descripcion: str = "",
):
    usuario = getattr(request, "user", None)
    ip = _get_client_ip(request)
    ua = request.META.get("HTTP_USER_AGENT", "")[:255]

    StudentLog.objects.create(
        usuario=usuario if usuario and usuario.is_authenticated else None,
        estudiante=estudiante,
        accion=accion,
        descripcion=descripcion,
        ip=ip,
        user_agent=ua,
    )
