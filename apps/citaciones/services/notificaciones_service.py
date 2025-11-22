# apps/citaciones/services/notificaciones_service.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils.timezone import now

from apps.notificaciones.models.notificacion import Notificacion


def notificar_citacion_aprobada(citacion, receptor_id: int) -> Notificacion:
    """
    Crea una notificación para la citación aprobada y la envía por WebSocket
    al usuario padre/madre/tutor con id = receptor_id.

    - Guarda un registro en la tabla notificaciones_notificacion
    - Marca estado_entrega = PENDIENTE (equivale a "no leída")
    - Rellena actualizado_en para evitar errores NOT NULL en MySQL
    - Publica un mensaje en el grupo "user-<id>" que consume el NotifConsumer
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
        enviada_en=ts,       # ts_creacion
        actualizado_en=ts,   # este campo es NOT NULL en la BD
        # entregada_en y leida_en se dejan en NULL (permitido)
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
