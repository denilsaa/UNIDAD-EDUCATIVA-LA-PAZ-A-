# apps/citaciones/ws.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone

# ============================
# Helpers para enviar eventos
# ============================

def push_propuesta_director(data: dict):
    """
    Propuesta de citación para el DIRECTOR (bandeja).
    data: {citacion_id, estudiante, motivo, razon, rho, Wq, sugerido}
    """
    ch = get_channel_layer()
    async_to_sync(ch.group_send)(
        "director_inbox",
        {"type": "director.citacion", "data": data}
    )

def push_citacion_padre(citacion, padre_id: int):
    """
    Notificación a PADRE cuando la citación queda AGENDADA.
    """
    ch = get_channel_layer()
    payload = {
        "type": "notify.unread",
        "event": "citacion",
        "citacion_id": citacion.id,
        "estudiante": str(citacion.estudiante),
        "mensaje": (citacion.motivo_resumen or "Nueva citación"),
        "cuando": timezone.now().isoformat(),
        "unread": 1,
    }
    async_to_sync(ch.group_send)(f"user_{padre_id}", payload)

def push_cola_state(data: dict):
    """
    Broadcast del estado de la cola (para panel de cola).
    data: libre, en_atencion, en_cola, etc.
    """
    ch = get_channel_layer()
    async_to_sync(ch.group_send)("cola_room", {"type": "cola.state", "data": data})

def push_dashboard_metrics(data: dict):
    """
    Broadcast de métricas del dashboard (λ̂, μ̂, ρ, Wq, Ws, etc.).
    """
    ch = get_channel_layer()
    async_to_sync(ch.group_send)("dashboard_room", {"type": "dashboard.metrics", "data": data})


# =======================================
# Consumers WebSocket usados en asgi.py
# =======================================

class ColaConsumer(AsyncJsonWebsocketConsumer):
    """
    WS simple para mostrar estado de la cola en tiempo real.
    Se une a 'cola_room' y escucha eventos type='cola.state'.
    """
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add("cola_room", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("cola_room", self.channel_name)

    # Mensajes entrantes desde group_send
    async def cola_state(self, event):
        # event = {"type": "cola.state", "data": {...}}
        await self.send_json({"type": "cola", "data": event.get("data", {})})

    # Opcional: eco de mensajes del cliente
    async def receive_json(self, content, **kwargs):
        # Puedes manejar comandos del front si quieres
        await self.send_json({"type": "ack", "recv": content})


class DashboardConsumer(AsyncJsonWebsocketConsumer):
    """
    WS para métricas M/M/1 del dashboard (λ̂, μ̂, ρ, Wq, Ws).
    Se une a 'dashboard_room' y escucha eventos type='dashboard.metrics'.
    """
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add("dashboard_room", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("dashboard_room", self.channel_name)

    async def dashboard_metrics(self, event):
        # event = {"type": "dashboard.metrics", "data": {...}}
        await self.send_json({"type": "dashboard", "data": event.get("data", {})})

    async def receive_json(self, content, **kwargs):
        await self.send_json({"type": "ack", "recv": content})
