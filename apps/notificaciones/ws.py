# apps/notificaciones/ws.py
import json
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer

class NotifConsumer(AsyncWebsocketConsumer):
    """
    DEV: como no usamos AuthMiddlewareStack,
    tomamos un user-id simulado desde la querystring ?uid=<id>
    Ejemplo de conexión: ws://localhost:8000/ws/notifs/?uid=1
    """
    async def connect(self):
        # Leer uid de la querystring (bytes -> str)
        query = parse_qs((self.scope.get("query_string") or b"").decode())
        uid = (query.get("uid") or ["anon"])[0]
        self.group_name = f"user_{uid}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        # Saludo
        await self.send(json.dumps({"type": "ws.connected", "group": self.group_name}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Handler para eventos de notificación
    async def notif_push(self, event):
        # event: {"type": "notif.push", "payload": {...}}
        await self.send(json.dumps({
            "type": "notif",
            "data": event.get("payload", {})
        }))
