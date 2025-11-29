# apps/citaciones/urls.py

from django.urls import path
from .views import bandeja

app_name = "citaciones"

urlpatterns = [
    path("pendientes/", bandeja.pendientes, name="pendientes"),
    path("agendadas/", bandeja.agendadas_rango, name="agendadas_rango"),
    path("agendadas/mis/", bandeja.agendadas_mis_cursos, name="agendadas_mis_cursos"),
    path("<int:pk>/aprobar/", bandeja.aprobar, name="aprobar"),
    path("<int:pk>/editar/", bandeja.editar, name="editar"),
    path("<int:pk>/editar-form/", bandeja.editar_form, name="editar_form"),
    path("<int:pk>/rechazar/", bandeja.rechazar, name="rechazar"),
    path("<int:pk>/notificar/", bandeja.notificar, name="notificar"),
]
