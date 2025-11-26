from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .models import StudentLog


def _get_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    StudentLog.objects.create(
        usuario=user,
        accion=StudentLog.Accion.LOGIN,
        descripcion="Ingreso al sistema",
        ip=_get_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    StudentLog.objects.create(
        usuario=user,
        accion=StudentLog.Accion.LOGOUT,
        descripcion="Salida del sistema",
        ip=_get_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
    )
