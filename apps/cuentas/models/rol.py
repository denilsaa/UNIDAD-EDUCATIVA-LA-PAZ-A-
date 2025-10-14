from django.db import models
from .base import SelladoTiempo

class Rol(SelladoTiempo):
    nombre = models.CharField(max_length=40, unique=True)

    class Meta:
        verbose_name = "rol"
        verbose_name_plural = "roles"

    def __str__(self):
        return self.nombre
