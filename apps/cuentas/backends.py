# apps/cuentas/backends.py
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from apps.cuentas.models import Usuario

class CustomBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Intentamos autenticar al usuario por su CI o email
        try:
            user = Usuario.objects.get(ci=username)  # Primero por CI
        except Usuario.DoesNotExist:
            try:
                user = Usuario.objects.get(email=username)  # Si no existe por CI, busca por email
            except Usuario.DoesNotExist:
                return None  # Si no existe, retornamos None

        # Compara la contraseña
        if user and user.check_password(password):  # Verifica la contraseña con el método `check_password`
            return user  # Si la contraseña es correcta, retorna el usuario

        return None
