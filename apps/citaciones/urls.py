from django.urls import path
from .views import bandeja

app_name = "citaciones"

urlpatterns = [
    path("pendientes/", bandeja.pendientes, name="pendientes"),
    path("agendadas/", bandeja.agendadas_rango, name="agendadas_rango"),  # <— NUEVA (rango)
    path("<int:pk>/aprobar/", bandeja.aprobar, name="aprobar"),
    path("<int:pk>/editar/", bandeja.editar, name="editar"),                # AJAX
    path("<int:pk>/editar-form/", bandeja.editar_form, name="editar_form"), # página
    path("<int:pk>/rechazar/", bandeja.rechazar, name="rechazar"),
]
