# apps/cursos/urls.py
from django.urls import path
from .views.cursos import (
    lista_cursos, crear_curso, ver_curso, editar_curso, eliminar_curso
)

app_name = "cursos"

urlpatterns = [
    path("", lista_cursos, name="lista_cursos"),
    path("crear/", crear_curso, name="crear_curso"),
    path("<int:curso_id>/", ver_curso, name="ver_curso"),
    path("<int:curso_id>/editar/", editar_curso, name="editar_curso"),
    path("<int:curso_id>/eliminar/", eliminar_curso, name="eliminar_curso"),
]
