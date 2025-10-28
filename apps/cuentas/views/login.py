from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib import messages
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
import re

from apps.cuentas.models import Usuario

BACKEND_PATH = 'apps.cuentas.backends.CustomBackend'

# ✅ Reglas
CI_RE = re.compile(r'^\d{1,8}$')  # solo números, 1–8 dígitos

@never_cache
@ensure_csrf_cookie
def login_view(request):
    """
    Login por CI + password (sin email).
    - Usuario: solo números (1–8 dígitos). Sin espacios.
    - Password: obligatoria, máx 50 caracteres.
    - Respeta ?next= y redirige por rol si no hay next.
    - Usa is_activo.
    """
    if request.method == 'POST':
        username_raw = request.POST.get('username') or ''
        password     = request.POST.get('password') or ''
        next_url     = request.GET.get('next')

        # 🔒 Validaciones de formato
        if re.search(r'\s', username_raw):
            messages.error(request, "El usuario no debe contener espacios.")
            return redirect('login')

        if not CI_RE.fullmatch(username_raw):
            messages.error(request, "El CI debe ser solo números (1–8 dígitos).")
            return redirect('login')

        if len(password) == 0 or len(password) > 50:
            messages.error(request, "La contraseña es obligatoria y debe tener máximo 50 caracteres.")
            return redirect('login')

        # 🔎 Buscar solo por CI
        try:
            user = Usuario.objects.get(ci=username_raw)
        except Usuario.DoesNotExist:
            user = None

        # ✅ Credenciales
        if user and user.check_password(password):
            if not getattr(user, "is_activo", True):
                messages.error(request, "Tu usuario está inactivo.")
                return redirect('login')

            auth_login(request, user, backend=BACKEND_PATH)
            request.session.set_expiry(0)  # expira al cerrar el navegador
            list(messages.get_messages(request))  # limpia mensajes

            if next_url:
                return redirect(next_url)

            # 🔀 Redirección por rol
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
