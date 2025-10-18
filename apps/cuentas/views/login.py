from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib import messages
from django.conf import settings

from apps.cuentas.models import Usuario

# Cambia esta constante si tu backend tiene otra ruta
BACKEND_PATH = 'apps.cuentas.backends.CustomBackend'
# Si prefieres usar el de Django, cambia a:
# BACKEND_PATH = 'django.contrib.auth.backends.ModelBackend'

def login_view(request):
    """
    Login por CI o Email + password.
    Respeta ?next=/ruta/protegida y redirige por rol si no hay next.
    NO modifica tu modelo. Usa is_activo para el estado.
    """
    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()   # CI o Email
        password = request.POST.get('password') or ''
        next_url = request.GET.get('next')

        user = None
        # 1) Buscar por CI
        try:
            user = Usuario.objects.get(ci=username)
        except Usuario.DoesNotExist:
            # 2) Buscar por email
            try:
                user = Usuario.objects.get(email=username)
            except Usuario.DoesNotExist:
                user = None

        # Validación de credenciales
        if user and user.check_password(password):
            # Tu modelo usa is_activo (no is_active)
            if not getattr(user, "is_activo", True):
                messages.error(request, "Tu usuario está inactivo.")
                return render(request, 'login.html')

            # Iniciar sesión: como hay múltiples backends, debemos indicar uno
            auth_login(request, user, backend=BACKEND_PATH)
            request.session.set_expiry(0)  # expira al cerrar el navegador

            # Respeta ?next=
            if next_url:
                return redirect(next_url)

            # Redirección por rol (ajusta si tus nombres difieren)
            rol_nombre = (getattr(user.rol, "nombre", "") or "").strip().lower()
            if rol_nombre == "director":
                return redirect('cuentas:director_dashboard')
            elif rol_nombre == "regente":
                return redirect('cuentas:regente_dashboard')
            elif rol_nombre == "secretaria":
                return redirect('cuentas:secretaria_dashboard')
            elif rol_nombre in ("padre", "padre de familia"):
                return redirect('cuentas:padre_dashboard')

            # Fallback
            return redirect('cuentas:director_dashboard')

        messages.error(request, "Credenciales inválidas")

    # GET o POST inválido
    return render(request, 'login.html')


def logout_view(request):
    """Cierra sesión y redirige al LOGIN_URL (o /login/ por defecto)."""
    auth_logout(request)
    messages.info(request, "Sesión cerrada.")
    login_url = getattr(settings, "LOGIN_URL", "/login/")
    return redirect(login_url)
