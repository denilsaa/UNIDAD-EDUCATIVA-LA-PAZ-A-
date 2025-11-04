# apps/citaciones/services/notificaciones_service.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils.timezone import now
from apps.notificaciones.models.notificacion import Notificacion

def notificar_citacion_aprobada(citacion, receptor_id: int):
    # 1) Persistir para el badge/panel
    Notificacion.objects.create(
        usuario_destino_id=receptor_id,
        citacion_id=citacion.id,
        titulo="Citación aprobada",
        cuerpo=f"Tu citación fue aprobada para {citacion.fecha_citacion} {citacion.hora_citacion}.",
        data={"tipo": "CITACION_APROBADA", "citacion_id": citacion.id, "estudiante_id": citacion.estudiante_id},
        estado_entrega="PENDIENTE",
        enviada_en=now(),
    )
    # 2) Empujar por WebSocket
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(
        f"user-{receptor_id}",
        {"type": "push", "data": {
            "tipo": "CITACION_APROBADA",
            "citacion_id": citacion.id,
            "titulo": "Citación aprobada",
        }},
    )
