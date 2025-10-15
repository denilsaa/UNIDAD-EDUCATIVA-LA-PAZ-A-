# apps/cuentas/urls.py

from django.urls import path
from django.views.generic import TemplateView, RedirectView

from .views.login import login_view
from .views.director_dashboard import director_dashboard

app_name = "cuentas"

urlpatterns = [
    path("", login_view, name="login"),
    path("login/", login_view, name="login"),

    # Dashboards
    path("dashboard/director/", director_dashboard, name="director_dashboard"),

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

    # Home (puedes cambiarlo luego)
    path("home/", RedirectView.as_view(pattern_name="cuentas:login", permanent=False), name="home"),
]
