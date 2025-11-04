# apps/notificaciones/ws.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from urllib.parse import parse_qs

class NotifConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        qs = parse_qs(self.scope["query_string"].decode())
        uid = (qs.get("uid") or [None])[0]
        if not uid:
            await self.close(); return
        self.group = f"user-{uid}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def push(self, event):
        await self.send_json(event["data"])
