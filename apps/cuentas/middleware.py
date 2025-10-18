# apps/cuentas/middleware.py
class DisableClientCacheMiddleware:
    """
    Evita que páginas vistas logueado queden en la caché del navegador.
    Así, tras logout, el botón Atrás no muestra el panel.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"
        return response
# apps/cuentas/middleware.py  (mismo archivo, debajo de la clase anterior)
import re
from django.shortcuts import redirect
from django.conf import settings

EXEMPT_URLS = [
    re.compile(r"^/login/?$"),
    re.compile(r"^/logout/?$"),
    re.compile(r"^/accounts/login/?$"),   # por compatibilidad
    re.compile(r"^/static/"),             # archivos estáticos
    re.compile(r"^/media/"),              # si usas media
]

class AuthRequiredMiddleware:
    """
    Redirige a LOGIN_URL si un usuario anónimo intenta acceder a rutas no exentas.
    Útil para proteger todo el sitio sin decorar cada vista.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        if any(pattern.match(path) for pattern in EXEMPT_URLS):
            return self.get_response(request)

        if not request.user.is_authenticated:
            login_url = getattr(settings, "LOGIN_URL", "/login/")
            return redirect(f"{login_url}?next={path}")

        return self.get_response(request)
