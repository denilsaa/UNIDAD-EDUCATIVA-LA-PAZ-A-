from django.db import models
from .estudiante import Estudiante
from .kardex_item import KardexItem
from apps.cuentas.models import Usuario

class KardexRegistro(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name="kardex_registros")
    kardex_item = models.ForeignKey(KardexItem, on_delete=models.RESTRICT)
    fecha = models.DateField()
    hora = models.TimeField(null=True, blank=True)
    observacion = models.CharField(max_length=255, null=True, blank=True)
    sello_maestro = models.BooleanField(default=False)
    docente = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name="marcas_kardex")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["estudiante", "fecha"]),
            models.Index(fields=["kardex_item"]),
        ]
        ordering = ["fecha", "hora", "id"]
        verbose_name = "registro de kárdex"
        verbose_name_plural = "registros de kárdex"

    def __str__(self):
        return f"{self.estudiante} - {self.kardex_item} ({self.fecha})"
