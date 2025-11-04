# apps/citaciones/ws.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ColaConsumer(AsyncWebsocketConsumer):
    group_name = "cola"

    async def connect(self):
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send(json.dumps({"type": "ws.connected", "group": self.group_name}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def cola_update(self, event):
        # event: {"type": "cola.update", "payload": {...}}
        await self.send(json.dumps({"type": "cola", "data": event.get("payload", {})}))

class DashboardConsumer(AsyncWebsocketConsumer):
    group_name = "dashboard"

    async def connect(self):
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send(json.dumps({"type": "ws.connected", "group": self.group_name}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def dashboard_metrics(self, event):
        # event: {"type": "dashboard.metrics", "payload": {...}}
        await self.send(json.dumps({"type": "metrics", "data": event.get("payload", {})}))
