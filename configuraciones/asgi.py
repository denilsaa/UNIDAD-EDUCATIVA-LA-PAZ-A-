# configuraciones/asgi.py

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "configuraciones.settings")  # 👈 PRIMERO

from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()  # 👈 configura settings aquí

# Recién ahora importa Channels y tus consumers
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path

# 👇 Consumers (importa DESPUÉS de get_asgi_application)
from apps.notificaciones.ws import NotifConsumer
from apps.citaciones.ws import ColaConsumer, DashboardConsumer

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter([
        path("ws/notifs/", NotifConsumer.as_asgi()),
        path("ws/cola/", ColaConsumer.as_asgi()),
        path("ws/dashboard/", DashboardConsumer.as_asgi()),
    ]),
})
