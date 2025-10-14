from django.db import models
from .estudiante import Estudiante

class Asistencia(models.Model):
    class Estado(models.TextChoices):
        PRESENTE = "PRESENTE", "Presente"
        FALTA = "FALTA", "Falta"
        ATRASO = "ATRASO", "Atraso"

    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name="asistencias")
    fecha = models.DateField()
    estado = models.CharField(max_length=10, choices=Estado.choices)
    observacion = models.CharField(max_length=255, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["estudiante", "fecha"], name="uq_asistencia_dia"),
        ]
        indexes = [models.Index(fields=["fecha"])]
        verbose_name = "asistencia"
        verbose_name_plural = "asistencias"

    def __str__(self):
        return f"{self.estudiante} - {self.fecha} ({self.estado})"
