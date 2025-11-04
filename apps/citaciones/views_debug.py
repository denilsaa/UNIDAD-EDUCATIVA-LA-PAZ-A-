# apps/citaciones/views_debug.py
from django.http import JsonResponse, HttpResponseForbidden
from django.conf import settings
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def _allow(request):
    """
    Permite usar /debug/ws/... solo si:
    - settings.DEBUG es True, y
    - el usuario está autenticado.
    NO usa is_staff (tu modelo Usuario no lo tiene).
    """
    if not settings.DEBUG:
        return False
    u = getattr(request, "user", None)
    return bool(getattr(u, "is_authenticated", False))

def ping_notifs(request):
    if not _allow(request):
        return HttpResponseForbidden("Solo DEBUG + autenticado.")
    uid = request.GET.get("uid", "1")
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(
        f"user_{uid}",
        {"type": "notif.push",
         "payload": {"title": "Citación AGENDADA", "msg": "Ejemplo DEV", "unread": 3}}
    )
    return JsonResponse({"ok": True, "sent_to": f"user_{uid}"})

def ping_cola(request):
    if not _allow(request):
        return HttpResponseForbidden("Solo DEBUG + autenticado.")
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(
        "cola",
        {"type": "cola.update",
         "payload": {"items": [{"id": 1, "estado": "EN_COLA", "hora": "09:00"}]}}
    )
    return JsonResponse({"ok": True})

def ping_dashboard(request):
    if not _allow(request):
        return HttpResponseForbidden("Solo DEBUG + autenticado.")
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(
        "dashboard",
        {"type": "dashboard.metrics",
         "payload": {"lambda_hat": 6, "mu_hat": 7, "rho": 0.86, "Wq_min": 12, "Ws_min": 38}}
    )
    return JsonResponse({"ok": True})
