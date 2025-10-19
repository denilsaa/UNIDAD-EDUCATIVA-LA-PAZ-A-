from django.urls import path
from apps.estudiantes.views.estudiante import (
    EstudianteListView, EstudianteCreateView, EstudianteUpdateView, EstudianteDeleteView,
    EstudiantesPorCursoListView,
)
from apps.estudiantes.views.forms_kardex import (
    kardex_registro_nuevo, kardex_registro_listar,
)
from apps.estudiantes.views.kardex_item import (
    KardexItemListView, KardexItemCreateView, KardexItemUpdateView, KardexItemDeleteView,
)

app_name = "estudiantes"

urlpatterns = [
    path("", EstudianteListView.as_view(), name="listar"),
    path("nuevo/", EstudianteCreateView.as_view(), name="crear"),
    path("<int:pk>/editar/", EstudianteUpdateView.as_view(), name="editar"),
    path("<int:pk>/eliminar/", EstudianteDeleteView.as_view(), name="eliminar"),

    path("curso/<int:curso_id>/", EstudiantesPorCursoListView.as_view(), name="por_curso"),

    # Kárdex (registros diarios por estudiante)
    path("kardex/<int:estudiante_id>/", kardex_registro_listar, name="kardex_listar"),
    path("kardex/<int:estudiante_id>/nuevo/", kardex_registro_nuevo, name="kardex_nuevo"),

    # Catálogo de ítems (KardexItem)
    path("kardex-items/", KardexItemListView.as_view(), name="kardex_items_listar"),
    path("kardex-items/nuevo/", KardexItemCreateView.as_view(), name="kardex_items_nuevo"),
    path("kardex-items/<int:pk>/editar/", KardexItemUpdateView.as_view(), name="kardex_items_editar"),
    path("kardex-items/<int:pk>/eliminar/", KardexItemDeleteView.as_view(), name="kardex_items_eliminar"),
]
