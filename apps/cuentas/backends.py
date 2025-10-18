# apps/cuentas/backends.py
from django.contrib.auth import get_user_model

Usuario = get_user_model()

class CustomBackend:
    """
    Autenticación por CI o Email.
    Debe implementar get_user para que AuthenticationMiddleware reconstruya request.user.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        # Este método es opcional si haces login manual, pero lo dejamos útil para /admin o pruebas
        user = None
        # Buscar por CI
        try:
            user = Usuario.objects.get(ci=username)
        except Usuario.DoesNotExist:
            # Buscar por email
            try:
                user = Usuario.objects.get(email=username)
            except Usuario.DoesNotExist:
                user = None

        if user and user.check_password(password) and getattr(user, "is_activo", True):
            return user
        return None

    def get_user(self, user_id):
        try:
            return Usuario.objects.get(pk=user_id)
        except Usuario.DoesNotExist:
            return None
