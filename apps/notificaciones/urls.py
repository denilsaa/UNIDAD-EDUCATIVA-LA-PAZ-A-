# apps/notificaciones/urls.py
from django.urls import path
from .views import marcar_todas_leidas

app_name = "notificaciones"

urlpatterns = [
    path("marcar-leidas/", marcar_todas_leidas, name="marcar_todas_leidas"),
]
