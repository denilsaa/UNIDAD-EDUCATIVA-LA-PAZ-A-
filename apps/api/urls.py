from django.urls import path
from .views import api_login, api_perfil, api_asistencia, api_kardex, api_citaciones, api_regente_asistencia, api_regente_kardex, api_estudiantes_curso, api_kardex_items

urlpatterns = [
    path("login/", api_login),
    path("perfil/", api_perfil),
    path("asistencia/", api_asistencia),
    path("kardex/", api_kardex),
    path("citaciones/", api_citaciones),
    # Regente
    path("regente/asistencia/", api_regente_asistencia),
    path("regente/kardex/", api_regente_kardex),
    path("estudiantes-curso/", api_estudiantes_curso),
    path("kardex-items/", api_kardex_items),
]
