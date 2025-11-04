"""
URL configuration for configuraciones project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# configuraciones/urls.py
from django.contrib import admin
from django.urls import path, include
from apps.cuentas.views.login import login_view
from apps.cuentas.views.director_dashboard import director_dashboard
from apps.cuentas.views_dev import dev_404
from django.conf import settings

urlpatterns = [
    path("", login_view, name="home"),                      # ⬅️ raíz = login
    path("login/", login_view, name="login"),
    path("dashboard/director/", director_dashboard, name="director_dashboard"),
    path("cuentas/", include(("apps.cuentas.urls", "cuentas"), namespace="cuentas")),
    path("cursos/", include("apps.cursos.urls")),
    path("estudiantes/", include("apps.estudiantes.urls")),
    path("admin/", admin.site.urls),
    path("dev/404/", dev_404, name="dev_404"),
]
if settings.DEBUG:
    from apps.citaciones.views_debug import ping_notifs, ping_cola, ping_dashboard
    urlpatterns += [
        path("debug/ws/notifs/", ping_notifs),
        path("debug/ws/cola/", ping_cola),
        path("debug/ws/dashboard/", ping_dashboard),
    ]
handler403 = "apps.cuentas.views.errors.error_403"
handler404 = "apps.cuentas.handlers.error_404"
