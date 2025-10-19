# apps/cursos/urls.py
from django.urls import path
from apps.cursos.views.cursos import (
    lista_cursos, crear_curso, ver_curso, editar_curso, eliminar_curso, mis_cursos_regente
)

app_name = "cursos"

urlpatterns = [
    path("", lista_cursos, name="lista_cursos"),                 # solo director
    path("nuevo/", crear_curso, name="crear_curso"),            # solo director
    path("<int:curso_id>/", ver_curso, name="ver_curso"),       # director o regente dueño
    path("<int:curso_id>/editar/", editar_curso, name="editar_curso"),  # solo director
    path("<int:curso_id>/eliminar/", eliminar_curso, name="eliminar_curso"),  # solo director

    # regente
    path("mis-cursos/", mis_cursos_regente, name="mis_cursos_regente"),
]
