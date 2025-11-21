# apps/citaciones/services/queue_service.py
from django.utils.timezone import now
from django.db import transaction
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.citaciones.models.citacion import Citacion
from apps.citaciones.services.agenda_service import agendar, reordenar_dia_por_peso
from apps.citaciones.services.metrics_service import metrics_payload
from apps.citaciones.services.notify_service import resolve_padres_ids
from apps.citaciones.ws import push_citacion_padre


COLA_GROUP = "cola_room"          # ← coincide con tu ColaConsumer
DASH_GROUP = "dashboard_room"     # ← coincide con tu DashboardConsumer


def _broadcast_cola(data: dict):
    layer = get_channel_layer()
    if not layer:
        return
    # Tu consumer espera type="cola.state"
    async_to_sync(layer.group_send)(COLA_GROUP, {"type": "cola.state", "data": data})


def _broadcast_dashboard_metrics(data: dict):
    layer = get_channel_layer()
    if not layer:
        return
    # Tu consumer espera type="dashboard.metrics"
    async_to_sync(layer.group_send)(DASH_GROUP, {"type": "dashboard.metrics", "data": data})


@transaction.atomic
def aprobar(citacion_id: int, usuario) -> Citacion:
    """Aprueba una citación, la agenda y reordena el día por peso (duracion_min)."""
    c = Citacion.objects.select_for_update().get(id=citacion_id)

    # Solo tiene sentido aprobar si estaba ABIERTA
    if c.estado != Citacion.Estado.ABIERTA:
        return c

    c.aprobado_por = usuario
    c.aprobado_en = now()
    c.save(update_fields=["aprobado_por", "aprobado_en", "actualizado_en"])

    # Asignar primer slot libre (M/M/1 estándar)
    agendar(c, c.duracion_min)

    # Reordenar todo el día por peso: el que tiene más duración va primero
    if c.fecha_citacion:
        reordenar_dia_por_peso(c.fecha_citacion)

    # payload para la cola (bandeja/visor de cola)
    cola_payload = {
        "id": c.id,
        "estado": c.estado,
        "fecha": c.fecha_citacion.isoformat() if c.fecha_citacion else None,
        "hora": c.hora_citacion.strftime("%H:%M") if c.hora_citacion else None,
        "duracion_min": c.duracion_min,
    }
    _broadcast_cola(cola_payload)

    # métricas para dashboard (M/M/1)
    _broadcast_dashboard_metrics(metrics_payload())

    # Notificar a los padres por WS (si hay canal)
    try:
        for padre_id in resolve_padres_ids(c.estudiante):
            push_citacion_padre(c, padre_id=padre_id)
    except Exception:
        # no queremos que un fallo de WS rompa la aprobación
        pass

    return c


def editar(citacion_id: int, fecha, hora, duracion_min: int | None, usuario) -> Citacion:
    c = Citacion.objects.get(id=citacion_id)
    c.fecha_citacion = fecha
    c.hora_citacion = hora
    if duracion_min:
        c.duracion_min = duracion_min
    c.estado = Citacion.Estado.AGENDADA
    c.aprobado_por = c.aprobado_por or usuario
    c.aprobado_en = c.aprobado_en or now()
    c.save()

    _broadcast_cola({
        "id": c.id,
        "estado": c.estado,
        "fecha": c.fecha_citacion.isoformat() if c.fecha_citacion else None,
        "hora": c.hora_citacion.strftime("%H:%M") if c.hora_citacion else None,
        "duracion_min": c.duracion_min,
    })
    _broadcast_dashboard_metrics(metrics_payload())
    return c


def rechazar(citacion_id: int, usuario) -> Citacion:
    c = Citacion.objects.get(id=citacion_id)
    c.estado = Citacion.Estado.CANCELADA
    c.aprobado_por = c.aprobado_por or usuario
    c.aprobado_en = c.aprobado_en or now()
    c.save(update_fields=["estado", "aprobado_por", "aprobado_en", "actualizado_en"])

    _broadcast_cola({"id": c.id, "estado": c.estado})
    _broadcast_dashboard_metrics(metrics_payload())
    return c
