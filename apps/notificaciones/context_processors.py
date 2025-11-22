# apps/notificaciones/context_processors.py
from apps.notificaciones.models.notificacion import Notificacion


def notificaciones_panel(request):
    """
    Context processor para el dashboard.

    Devuelve las notificaciones del usuario actual para mostrarlas siempre
    en el panel lateral (campanita), incluso después de recargar la página.

    Variables que expone en los templates:
      - notif_panel_list   → queryset con las últimas 20 notificaciones
      - notif_panel_unread → cantidad de notificaciones PENDIENTE (no leídas)
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}

    # Últimas 20 notificaciones del usuario
    notif_qs = (
        Notificacion.objects
        .filter(usuario_destino_id=user.id)
        .order_by("-enviada_en")[:20]
    )

    # Cantidad de no leídas / pendientes
    unread_count = Notificacion.objects.filter(
        usuario_destino_id=user.id,
        estado_entrega=Notificacion.Estado.PENDIENTE,
    ).count()

    return {
        "notif_panel_list": notif_qs,
        "notif_panel_unread": unread_count,
    }
