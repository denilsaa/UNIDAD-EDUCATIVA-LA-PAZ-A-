# apps/cuentas/middleware.py

import re
from django.conf import settings
from django.shortcuts import redirect
from django.db import connections, close_old_connections
from django.core.cache import cache
from django.urls import resolve
from django.contrib import messages


# ==============================
# 1) Throttle/Dedup de LOGIN
# ==============================
class ThrottleLoginMiddleware:
    """
    Deduplica/limita POSTs al login para evitar múltiples intentos simultáneos
    (doble click/enter) que abren conexiones extra a la BD.

    Por defecto permite SOLO el primer POST en una ventana de 3 segundos.
    Si quieres permitir hasta 3, cambia MAX_PER_WINDOW = 3.
    """
    WINDOW_SECONDS = 3
    MAX_PER_WINDOW = 1  # Cambia a 3 si quieres aceptar hasta 3 clicks por 3s

    def __init__(self, get_response):
        self.get_response = get_response

    def _client_ip(self, request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "0.0.0.0")

    def _is_login_path(self, request):
        path = request.path_info.rstrip("/")
        try:
            match = resolve(request.path_info)
            if match and match.url_name in {"login"}:
                return True
        except Exception:
            pass
        return path.endswith("/login")

    def __call__(self, request):
        # Solo aplicamos a POST del login
        if request.method == "POST" and self._is_login_path(request):
            username = (request.POST.get("username") or "").strip().lower()
            ip = self._client_ip(request)

            if self.MAX_PER_WINDOW <= 1:
                # Modo "solo el primero cuenta"
                lock_key = f"login:lock:{ip}:{username}"
                if not cache.add(lock_key, "1", timeout=self.WINDOW_SECONDS):
                    #messages.info(request, "Ya estamos procesando tu ingreso…")
                    login_url = getattr(settings, "LOGIN_URL", "/login/")
                    return redirect(login_url)
            else:
                # Modo "acepta hasta N por ventana"
                count_key = f"login:count:{ip}:{username}"
                count = cache.get(count_key, 0)
                if count >= self.MAX_PER_WINDOW:
                    messages.warning(request, "Demasiados intentos seguidos. Espera unos segundos.")
                    login_url = getattr(settings, "LOGIN_URL", "/login/")
                    return redirect(login_url)
                cache.set(count_key, count + 1, timeout=self.WINDOW_SECONDS)

        return self.get_response(request)


# ==============================
# 2) Cache-Control (no-store)
# ==============================
class DisableClientCacheMiddleware:
    """
    Evita que páginas sensibles queden en la caché del navegador:
    - Cuando el usuario está autenticado (paneles, etc.)
    - En /login y /logout (para evitar reusar formularios/CSRF viejos)
    Así, tras logout, el botón Atrás no muestra el panel cacheado.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def _is_sensitive(self, request):
        path = request.path_info
        # Autenticado o rutas de login/logout o zonas de dashboard
        try:
            match = resolve(path)
            view_name = match.url_name
        except Exception:
            view_name = None

        return (
            (getattr(request, "user", None) and request.user.is_authenticated)
            or path.startswith("/dashboard")
            or view_name in {"login", "logout"}
            or path.rstrip("/").endswith(("/login", "/logout"))
        )

    def __call__(self, request):
        response = self.get_response(request)
        if self._is_sensitive(request):
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"
        return response


# ==============================
# 3) Rutas exentas de autenticación
# ==============================
EXEMPT_URLS = [
    re.compile(r"^/login/?$"),
    re.compile(r"^/logout/?$"),
    re.compile(r"^/accounts/login/?$"),   # por compatibilidad
    re.compile(r"^/static/"),             # archivos estáticos
    re.compile(r"^/media/"),              # si usas media
]


# ==============================
# 4) AuthRequired (protege todo)
# ==============================
class AuthRequiredMiddleware:
    """
    Redirige a LOGIN_URL si un usuario anónimo intenta acceder a rutas no exentas.
    Requiere que 'django.contrib.auth.middleware.AuthenticationMiddleware' esté antes en MIDDLEWARE.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info

        # Permitir rutas API y WebSockets sin redirección ni render HTML
        if path.startswith("/api/") or path.startswith("/ws/"):
            return self.get_response(request)

        # Permitir las rutas exentas
        if any(pattern.match(path) for pattern in EXEMPT_URLS):
            return self.get_response(request)

        # Si no está autenticado, redirigir a login con next=path
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated):
            login_url = getattr(settings, "LOGIN_URL", "/login/")
            return redirect(f"{login_url}?next={path}")

        return self.get_response(request)


# ==============================
# 5) Última URL OK (tracking suave)
# ==============================
class LastOKURLMiddleware:
    """
    Guarda en sesión la última URL interna GET que devolvió 200.
    Útil para redirigir desde handler404 a una página previa válida.
    """
    SESSION_KEY = "cuentas:last_ok_path"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        try:
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


# ==============================
# 6) Cierre proactivo de conexiones
# ==============================
class CloseDBConnectionsMiddleware:
    """
    Cierra conexiones viejas/obsoletas al inicio y fin de cada request.
    Evita superar el límite de max_user_connections en proveedores con tope bajo.
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
                try:
                    conn.close_if_unusable_or_obsolete()
                except Exception:
                    pass
                try:
                    conn.close()
                except Exception:
                    pass
