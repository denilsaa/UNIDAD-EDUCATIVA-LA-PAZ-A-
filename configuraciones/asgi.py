"""
ASGI config for configuraciones project.
DEV: WebSockets sin AuthMiddlewareStack para evitar hits a BD (max_user_connections).
"""
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path

# 👇 Consumers
from apps.notificaciones.ws import NotifConsumer
from apps.citaciones.ws import ColaConsumer, DashboardConsumer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "configuraciones.settings")

django_asgi_app = get_asgi_application()

# ⚠️ DEV: sin AuthMiddlewareStack en websocket para no tocar la BD en handshake
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter([
        path("ws/notifs/", NotifConsumer.as_asgi()),
        path("ws/cola/", ColaConsumer.as_asgi()),
        path("ws/dashboard/", DashboardConsumer.as_asgi()),
    ]),
})
