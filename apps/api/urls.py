from django.urls import path
from .views import api_login, api_perfil, api_asistencia, api_kardex

urlpatterns = [
    path("login/", api_login),
    path("perfil/", api_perfil),
    path("asistencia/", api_asistencia),
    path("kardex/", api_kardex),
]
