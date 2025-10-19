# apps/cuentas/mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .roles import has_any_role

class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Uso en CBV:
      class MiVista(RoleRequiredMixin, ListView):
          required_roles = ("director","secretaria")
    """
    required_roles = tuple()

    def test_func(self):
        return has_any_role(self.request.user, *self.required_roles)
