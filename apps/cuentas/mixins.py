from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .roles import has_any_role

class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    required_roles = tuple()
    def test_func(self):
        return has_any_role(self.request.user, *self.required_roles)
