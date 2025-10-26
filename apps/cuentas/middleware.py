# apps/cuentas/middleware.py

import re
from django.conf import settings
from django.shortcuts import redirect
from django.db import connections, close_old_connections


class DisableClientCacheMiddleware:
    """
    Evita que páginas vistas logueado queden en la caché del navegador.
    Así, tras logout, el botón Atrás no muestra el panel.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if getattr(request, "user", None) and request.user.is_authenticated:
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"
        return response


# Rutas exentas de autenticación
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
    Requiere que 'django.contrib.auth.middleware.AuthenticationMiddleware' esté antes en MIDDLEWARE.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info

        # Permitir las rutas exentas
        if any(pattern.match(path) for pattern in EXEMPT_URLS):
            return self.get_response(request)

        # Si no está autenticado, redirigir a login con next=path
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated):
            login_url = getattr(settings, "LOGIN_URL", "/login/")
            return redirect(f"{login_url}?next={path}")

        return self.get_response(request)


class LastOKURLMiddleware:
    """
    Guarda en sesión la última URL interna GET que devolvió 200.
    Permite que la vista handler404 redirija automáticamente a esa página
    (por ejemplo, después de mostrar una pantalla 404 con contador de 5 s).

    La vista 404 debería leer 'request.session["cuentas:last_ok_path"]'
    y usarla como previous_url.
    """
    SESSION_KEY = "cuentas:last_ok_path"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        try:
            # Solo guardamos en peticiones GET internas con respuesta 200.
            if (
                request.method == "GET"
                and request.path.startswith("/")
                and getattr(response, "status_code", None) == 200
            ):
                request.session[self.SESSION_KEY] = request.get_full_path()
        except Exception:
            # Nunca bloquear el request por errores de tracking.
            pass

        return response

class CloseDBConnectionsMiddleware:
    """
    Cierra conexiones viejas/obsoletas al inicio y fin de cada request.
    Evita superar el límite bajo de max_user_connections (Clever Cloud).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Antes de procesar la vista
        close_old_connections()

        try:
            response = self.get_response(request)
            return response
        finally:
            # Después de procesar la vista
            for conn in connections.all():
                # Cierra si está obsoleta o en mal estado
                conn.close_if_unusable_or_obsolete()
                # Y fuerza el cierre para no dejar conexiones vivas
                try:
                    conn.close()
                except Exception:
                    pass