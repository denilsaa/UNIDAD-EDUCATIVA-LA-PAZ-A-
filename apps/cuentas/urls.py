# apps/cuentas/urls.py
from django.urls import path
from django.views.generic import TemplateView, RedirectView

from .views.login import login_view, logout_view
from .views.director_dashboard import director_dashboard
from .views.usuarios import (
    crear_usuario, lista_usuarios, ver_usuario, editar_usuario, eliminar_usuario
)

app_name = "cuentas"

urlpatterns = [
    # Login / Logout
    path("", login_view, name="login"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),

    # Alias de compatibilidad (por si algo redirige a /accounts/...)
    path("accounts/login/", RedirectView.as_view(pattern_name="cuentas:login")),
    path("accounts/logout/", RedirectView.as_view(pattern_name="cuentas:logout")),

    # Dashboards
    path("dashboard/director/",  director_dashboard, name="director_dashboard"),
    path(
        "dashboard/regente/",
        TemplateView.as_view(template_name="dashboard/regente_dashboard.html"),
        name="regente_dashboard",
    ),
    path(
        "dashboard/secretaria/",
        TemplateView.as_view(template_name="dashboard/secretaria_dashboard.html"),
        name="secretaria_dashboard",
    ),
    path(
        "dashboard/padre/",
        TemplateView.as_view(template_name="dashboard/padre_dashboard.html"),
        name="padre_dashboard",
    ),

    # CRUD usuarios
    path("usuarios/crear/", crear_usuario, name="crear_usuario"),
    path("usuarios/", lista_usuarios, name="lista_usuarios"),
    path("usuarios/<int:user_id>/", ver_usuario, name="ver_usuario"),
    path("usuarios/<int:user_id>/editar/", editar_usuario, name="editar_usuario"),
    path("usuarios/<int:user_id>/eliminar/", eliminar_usuario, name="eliminar_usuario"),
]
