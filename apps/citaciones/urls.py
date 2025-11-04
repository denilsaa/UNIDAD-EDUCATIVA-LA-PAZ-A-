from django.urls import path
from .views import aprobacion  # ahora sí es un paquete

app_name = "citaciones"

urlpatterns = [
    path("pendientes/", aprobacion.pendientes, name="pendientes"),
    path("<int:pk>/aprobar/", aprobacion.aprobar, name="aprobar"),
    path("<int:pk>/rechazar/", aprobacion.rechazar, name="rechazar"),
    path("<int:pk>/editar/", aprobacion.editar, name="editar"),
]
