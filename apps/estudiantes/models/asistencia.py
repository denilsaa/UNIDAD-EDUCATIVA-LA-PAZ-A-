from django.db import models
from django.core.exceptions import ValidationError   # ← NUEVO
from datetime import date                            # ← NUEVO
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

    # ✅ Validación: solo lunes–viernes
    def clean(self):
        if self.fecha is None:
            return
        dow = self.fecha.weekday()  # 0=Lunes .. 6=Domingo
        if dow > 4:
            raise ValidationError("La asistencia solo se registra de lunes a viernes.")

    class Meta:
        # Ya tienes la unicidad por estudiante+fecha
        constraints = [
            models.UniqueConstraint(fields=["estudiante", "fecha"], name="uq_asistencia_dia"),
        ]
        # ✅ Índices útiles
        indexes = [
            models.Index(fields=["fecha"]),
            models.Index(fields=["estudiante", "fecha"]),   # ← NUEVO (compuesto)
        ]
        ordering = ["-fecha", "estudiante_id"]             # ← NUEVO (orden por defecto)
        verbose_name = "asistencia"
        verbose_name_plural = "asistencias"
        # (Opcional) permisos si los quieres usar en decorators o admin
        # permissions = [
        #     ("tomar_asistencia", "Puede tomar asistencia"),
        #     ("ver_asistencia", "Puede ver asistencia"),
        # ]

    def __str__(self):
        return f"{self.estudiante} - {self.fecha} ({self.estado})"
