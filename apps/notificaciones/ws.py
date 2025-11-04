# apps/notificaciones/ws.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

class NotifConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # === Identidad del usuario ===
        user = self.scope.get("user")
        uid = None
        role = ""

        if user and not isinstance(user, AnonymousUser) and user.is_authenticated:
            uid = getattr(user, "id", None)
            role = (getattr(getattr(user, "rol", None), "nombre", "") or "").lower()
        else:
            # DEV: sin AuthMiddlewareStack (usa ?uid=)
            try:
                from urllib.parse import parse_qs
                qs = parse_qs(self.scope["query_string"].decode())
                uid_param = qs.get("uid", [None])[0]
                uid = int(uid_param) if uid_param else None
                # si quieres, role por query string: ?role=director
                role = (qs.get("role", [""])[0] or "").lower()
            except Exception:
                uid = None

        self.uid = uid
        self.role = role

        # Aceptar siempre en dev; en prod puedes validar origen/host/rol
        await self.accept()

        # === Unirse a grupos ===
        if uid:
            await self.channel_layer.group_add(f"user_{uid}", self.channel_name)
        if "director" in role:
            await self.channel_layer.group_add("director_inbox", self.channel_name)

    async def disconnect(self, close_code):
        if getattr(self, "uid", None):
            await self.channel_layer.group_discard(f"user_{self.uid}", self.channel_name)
        if "director" in getattr(self, "role", ""):
            await self.channel_layer.group_discard("director_inbox", self.channel_name)

    # ====== Handlers que llegan desde group_send() ======

    async def notify_unread(self, event):
        """
        Notificación para PADRE (campana).
        event = {
          "type": "notify.unread",
          "event": "citacion",
          "unread": 1,
          "mensaje": "...",
          "citacion_id": ...,
          "estudiante": "...",
          "cuando": "...",
        }
        """
        await self.send_json({"type": "notif", "data": event})

    async def director_citacion(self, event):
        """
        Propuesta de citación para el DIRECTOR (bandeja).
        event = { "type": "director.citacion", "data": {...} }
        """
        await self.send_json({"type": "director_inbox", "data": event["data"]})
