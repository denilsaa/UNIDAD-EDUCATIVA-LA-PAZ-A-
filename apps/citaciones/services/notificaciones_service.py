# apps/citaciones/services/notificaciones_service.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils.timezone import now

from apps.notificaciones.models.notificacion import Notificacion


def notificar_citacion_aprobada(citacion, receptor_id: int) -> Notificacion:
    """
    Crea un registro en notificaciones_notificacion y envía un mensaje
    por WebSocket al padre/madre/tutor.

    Se asegura de rellenar 'actualizado_en' para evitar el error
    "Column 'actualizado_en' cannot be null".
    """
    ts = now()
    mensaje = (
        f"Tu citación fue aprobada para "
        f"{citacion.fecha_citacion} {citacion.hora_citacion}."
    )

    # 1) Guardar en BD (tabla notificaciones_notificacion)
    notif = Notificacion.objects.create(
        usuario_destino_id=receptor_id,
        citacion_id=citacion.id,
        titulo="Citación aprobada",
        cuerpo=mensaje,
        data={
            "tipo": "CITACION_APROBADA",
            "citacion_id": citacion.id,
            "estudiante_id": citacion.estudiante_id,
        },
        estado_entrega=Notificacion.Estado.PENDIENTE,
        enviada_en=ts,        # ts_creacion
        actualizado_en=ts,    # ⚠️ este campo es NOT NULL en MySQL
        # entregada_en y leida_en los dejamos en NULL (permitido)
    )

    # 2) Payload que espera base_dashboard.js en el WebSocket
    payload = {
        "type": "notify.unread",
        "event": "citacion",
        "citacion_id": citacion.id,
        "estudiante": str(citacion.estudiante),
        "mensaje": mensaje,
        "cuando": ts.isoformat(),
        "unread": 1,
    }

    layer = get_channel_layer()
    async_to_sync(layer.group_send)(
        f"user-{receptor_id}",          # coincide con NotifConsumer
        {"type": "push", "data": payload},
    )

    return notif
