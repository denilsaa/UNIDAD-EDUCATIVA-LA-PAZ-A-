from django.urls import path
from apps.estudiantes.views.estudiante import (
    EstudianteListView, EstudianteCreateView, EstudianteUpdateView, EstudianteDeleteView,
    EstudiantesPorCursoListView, EstudianteEliminarCompletoView
)
from apps.estudiantes.views.forms_kardex import (
    kardex_registro_nuevo, kardex_registro_listar,
)
from apps.estudiantes.views.kardex_item import (
    KardexItemListView, KardexItemCreateView, KardexItemUpdateView, KardexItemDeleteView,
)
from apps.estudiantes.views.padre import MisHijosListView, HijoDetalleView

# NUEVO
from apps.estudiantes.views.asistencia import (
    asistencia_calendario, asistencia_exclusiones, asistencia_exclusion_eliminar,
    asistencia_tomar, asistencia_padre_detalle,
)
from apps.estudiantes.views.kardex_item import kardex_item_existe

app_name = "estudiantes"

urlpatterns = [
    path("", EstudianteListView.as_view(), name="listar"),
    path("nuevo/", EstudianteCreateView.as_view(), name="crear"),
    path("<int:pk>/editar/", EstudianteUpdateView.as_view(), name="editar"),
    path("<int:pk>/eliminar/", EstudianteDeleteView.as_view(), name="eliminar"),

    path("curso/<int:curso_id>/", EstudiantesPorCursoListView.as_view(), name="por_curso"),

    # Kárdex
    path("kardex/<int:estudiante_id>/", kardex_registro_listar, name="kardex_listar"),
    path("kardex/<int:estudiante_id>/nuevo/", kardex_registro_nuevo, name="kardex_nuevo"),

    # Ítems Kárdex
    path("kardex-items/", KardexItemListView.as_view(), name="kardex_items_listar"),
    path("kardex-items/nuevo/", KardexItemCreateView.as_view(), name="kardex_items_nuevo"),
    path("kardex-items/<int:pk>/editar/", KardexItemUpdateView.as_view(), name="kardex_items_editar"),
    path("kardex-items/<int:pk>/eliminar/", KardexItemDeleteView.as_view(), name="kardex_items_eliminar"),
    path("kardex/items/existe/", kardex_item_existe, name="kardex_item_existe"),

    # Padre (ya tenías)
    path("mis-hijos/", MisHijosListView.as_view(), name="mis_hijos"),
    path("hijo/<int:estudiante_id>/", HijoDetalleView.as_view(), name="hijo_detalle"),

    # === NUEVO: Asistencia ===
    path("asistencia/calendario/", asistencia_calendario, name="asistencia_calendario"),
    path("asistencia/calendario/<int:cal_id>/exclusiones/", asistencia_exclusiones, name="asistencia_exclusiones"),
    path("asistencia/calendario/<int:cal_id>/exclusiones/<int:excl_id>/eliminar/", asistencia_exclusion_eliminar, name="asistencia_exclusion_eliminar"),
    path("asistencia/tomar/<int:curso_id>/", asistencia_tomar, name="asistencia_tomar"),
    path("asistencia/hijo/<int:estudiante_id>/", asistencia_padre_detalle, name="asistencia_padre_detalle"),
    path("<int:pk>/eliminar-completo/", EstudianteEliminarCompletoView.as_view(), name="eliminar_completo"),

]
