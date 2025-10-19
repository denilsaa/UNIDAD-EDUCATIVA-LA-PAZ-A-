from django.urls import path
from apps.estudiantes.views.estudiante import (
    EstudianteListView, EstudianteCreateView,
    EstudianteUpdateView, EstudianteDeleteView
)
from apps.estudiantes.views.forms_kardex import (
    kardex_registro_nuevo,
    kardex_registro_listar,
)
app_name = "estudiantes"

urlpatterns = [
    path("", EstudianteListView.as_view(), name="listar"),
    path("nuevo/", EstudianteCreateView.as_view(), name="crear"),
    path("<int:pk>/editar/", EstudianteUpdateView.as_view(), name="editar"),
    path("<int:pk>/eliminar/", EstudianteDeleteView.as_view(), name="eliminar"),
    path("kardex/<int:estudiante_id>/", kardex_registro_listar, name="kardex_listar"),
    path("kardex/<int:estudiante_id>/nuevo/", kardex_registro_nuevo, name="kardex_nuevo"),
]
