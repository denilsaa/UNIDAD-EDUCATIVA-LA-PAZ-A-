from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib import messages
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
import re

from apps.cuentas.models import Usuario

# Backend de autenticación a usar para auth_login
BACKEND_PATH = 'apps.cuentas.backends.CustomBackend'
# Si prefieres el de Django:
# BACKEND_PATH = 'django.contrib.auth.backends.ModelBackend'


@never_cache
@ensure_csrf_cookie
def login_view(request):
    """
    Login por CI o Email + password.
    - Rechaza *cualquier* espacio en el usuario.
    - Respeta ?next=/ruta/protegida y redirige por rol si no hay next.
    - Tu modelo usa is_activo (no is_active).
    """
    if request.method == 'POST':
        username_raw = request.POST.get('username') or ''
        password = request.POST.get('password') or ''
        next_url = request.GET.get('next')

        # No permitir espacios en el usuario (inicio/medio/fin)
        if re.search(r'\s', username_raw):
            messages.error(request, "El usuario no debe contener espacios.")
            return redirect('login')

        username = username_raw  # sin strip, para no "arreglar" entradas incorrectas

        # Buscar usuario por CI exacto o email case-insensitive
        user = None
        try:
            user = Usuario.objects.get(ci=username)
        except Usuario.DoesNotExist:
            try:
                user = Usuario.objects.get(email__iexact=username)
            except Usuario.DoesNotExist:
                user = None

        # Validar credenciales
        if user and user.check_password(password):
            if not getattr(user, "is_activo", True):
                messages.error(request, "Tu usuario está inactivo.")
                return redirect('login')

            auth_login(request, user, backend=BACKEND_PATH)
            request.session.set_expiry(0)  # expira al cerrar el navegador

            # Limpia mensajes pendientes para que no aparezcan en el dashboard
            list(messages.get_messages(request))

            if next_url:
                return redirect(next_url)

            rol_nombre = (getattr(user.rol, "nombre", "") or "").strip().lower()
            if rol_nombre == "director":
                return redirect('cuentas:director_dashboard')
            elif rol_nombre == "regente":
                return redirect('cuentas:regente_dashboard')
            elif rol_nombre in ("secretaria", "secretaría"):
                return redirect('cuentas:secretaria_dashboard')
            elif rol_nombre in ("padre", "padre de familia"):
                return redirect('cuentas:padre_dashboard')

            return redirect('cuentas:director_dashboard')

        messages.error(request, "Credenciales inválidas")
        return redirect('login')

    # GET
    return render(request, 'login.html')


@never_cache
def logout_view(request):
    """Cierra sesión y redirige al LOGIN_URL (o /login/ por defecto)."""
    auth_logout(request)
    try:
        request.session.flush()
    except Exception:
        pass
    messages.info(request, "Sesión cerrada.")
    login_url = getattr(settings, "LOGIN_URL", "/login/")
    return redirect(login_url)
