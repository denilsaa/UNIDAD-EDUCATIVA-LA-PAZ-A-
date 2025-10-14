from django.db import models
from .base import SelladoTiempo
from .rol import Rol

class Usuario(SelladoTiempo):
    rol = models.ForeignKey(Rol, on_delete=models.RESTRICT, related_name="usuarios")
    ci = models.CharField("CI", max_length=40, unique=True, null=True, blank=True)
    nombres = models.CharField(max_length=120)
    apellidos = models.CharField(max_length=120)
    email = models.EmailField(null=True, blank=True, unique=True)
    telefono = models.CharField(max_length=32, null=True, blank=True)
    password_hash = models.CharField(max_length=255)
    is_activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        return f"{self.apellidos}, {self.nombres}"
