# apps/cuentas/urls.py
from django.urls import path
from django.views.generic import RedirectView

from .views.login import login_view, logout_view
from .views.director_dashboard import director_dashboard
from .views.usuarios import (
    crear_usuario, lista_usuarios, ver_usuario, editar_usuario, eliminar_usuario, verificar_ci, buscar_usuarios,
    lista_personal, lista_padres, crear_personal, crear_padre, editar_personal, editar_padre
)
from apps.cuentas.views.dashboards import padre_dashboard, regente_dashboard, secretaria_dashboard

app_name = "cuentas"

urlpatterns = [
    # Login / Logout
    path("", login_view, name="login"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),

    # Alias de compatibilidad
    path("accounts/login/", RedirectView.as_view(pattern_name="cuentas:login")),
    path("accounts/logout/", RedirectView.as_view(pattern_name="cuentas:logout")),

    # Dashboards
    path("dashboard/director/", director_dashboard, name="director_dashboard"),
    path("dashboard/padre/", padre_dashboard, name="padre_dashboard"),
    path("dashboard/regente/", regente_dashboard, name="regente_dashboard"),
    path("dashboard/secretaria/", secretaria_dashboard, name="secretaria_dashboard"),

    # CRUD usuarios (legacy/compat)
    path("usuarios/crear/", crear_usuario, name="crear_usuario"),
    path("usuarios/", buscar_usuarios, name="lista_usuarios"),
    path("usuarios/<int:user_id>/", ver_usuario, name="ver_usuario"),
    path("usuarios/<int:user_id>/editar/", editar_usuario, name="editar_usuario"),
    path("usuarios/<int:user_id>/eliminar/", eliminar_usuario, name="eliminar_usuario"),

    # CRUD separado por sección
    # Personal administrativo
    path("personal/", lista_personal, name="lista_personal"),
    path("personal/nuevo/", crear_personal, name="crear_personal"),
    path("personal/<int:user_id>/editar/", editar_personal, name="editar_personal"),

    # Padres de familia
    path("padres/", lista_padres, name="lista_padres"),
    path("padres/nuevo/", crear_padre, name="crear_padre"),
    path("padres/<int:user_id>/editar/", editar_padre, name="editar_padre"),

    # Validación AJAX
    path("verificar-ci/", verificar_ci, name="verificar_ci"),
]
