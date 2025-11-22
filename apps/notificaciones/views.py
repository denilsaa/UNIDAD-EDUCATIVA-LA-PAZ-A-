# apps/notificaciones/views.py
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.timezone import now

from apps.notificaciones.models.notificacion import Notificacion


@login_required
def marcar_todas_leidas(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)

    ts = now()
    qs = Notificacion.objects.filter(
        usuario_destino=request.user,
        estado_entrega=Notificacion.Estado.PENDIENTE,
    )

    num = qs.update(
        estado_entrega=Notificacion.Estado.LEIDA,
        leida_en=ts,
        actualizado_en=ts,
    )

    return JsonResponse({"ok": True, "marcadas": num})
