from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from .rol import Rol
from .base import SelladoTiempo

class Usuario(SelladoTiempo, models.Model):
    rol = models.ForeignKey(Rol, on_delete=models.RESTRICT, related_name="usuarios")
    ci = models.CharField("CI", max_length=40, unique=True, null=True, blank=True)
    nombres = models.CharField(max_length=120)
    apellidos = models.CharField(max_length=120)
    email = models.EmailField(null=True, blank=True, unique=True)
    telefono = models.CharField(max_length=32, null=True, blank=True)
    password_hash = models.CharField(max_length=255)  # Guardar el hash de la contraseña
    is_activo = models.BooleanField(default=True)

    # Este es el campo que Django usará como identificador
    USERNAME_FIELD = 'ci'  
    REQUIRED_FIELDS = ['email']  # Indicar qué campos se deben usar al crear el superusuario

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        return f"{self.apellidos}, {self.nombres}"

    def set_password(self, raw_password):
        """Override set_password to use password_hash instead of password field"""
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        """Override check_password to compare password_hash"""
        return check_password(raw_password, self.password_hash)

    @property
    def is_authenticated(self):
        """Override is_authenticated to return True if the user is active."""
        return self.is_activo

    @property
    def is_anonymous(self):
        """Override is_anonymous to return False if the user is active."""
        return not self.is_activo
    # 👈 NUEVO: obtener nombre completo
    @property
    def get_full_name(self):
        return f"{self.nombres} {self.apellidos}"