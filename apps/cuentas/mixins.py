# apps/cuentas/mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render
from .roles import has_any_role

class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Úsalo en CBVs y define:
        required_roles = ("director", "secretaria", ...)
    """
    required_roles = tuple()

    def test_func(self):
        return has_any_role(self.request.user, *self.required_roles)

    def handle_no_permission(self):
        """
        Si no está logueado, LoginRequiredMixin ya redirige al login.
        Si está logueado pero no tiene rol, devolvemos 403 con la plantilla
        que incluye el contador de 5s para volver atrás.
        """
        return render(self.request, "403.html", status=403)
