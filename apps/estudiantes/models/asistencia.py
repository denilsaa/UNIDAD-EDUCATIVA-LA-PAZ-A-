from django.db import models
from django.core.exceptions import ValidationError
from datetime import date
from .estudiante import Estudiante


class Asistencia(models.Model):
    class Estado(models.TextChoices):
        PRESENTE = "PRESENTE", "Presente"
        FALTA    = "FALTA", "Falta"
        ATRASO   = "ATRASO", "Atraso"

    estudiante = models.ForeignKey(
        Estudiante,
        on_delete=models.CASCADE,
        related_name="asistencias",
    )
    fecha = models.DateField()
    estado = models.CharField(max_length=10, choices=Estado.choices)
    observacion = models.CharField(max_length=255, null=True, blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    # === Validaciones de dominio ===
    def clean(self):
        # 1) Fecha presente
        if self.fecha is None:
            raise ValidationError("La fecha es obligatoria.")

        # 2) Validar contra el calendario ACTIVO (rango, días hábiles, exclusiones)
        #    Import local para evitar ciclos
        from apps.estudiantes.models.asistencia_config import AsistenciaCalendario

        cal = (
            AsistenciaCalendario.objects
            .filter(activo=True)
            .order_by("-creado_en")
            .first()
        )

        if cal:
            if not cal.admite_fecha(self.fecha):
                raise ValidationError("La fecha no admite asistencia según el calendario activo.")
        else:
            # 👉 Alternativa: forzar que exista un calendario activo
            # raise ValidationError("No hay calendario de asistencia activo.")
            # Por ahora, si no hay calendario activo, no bloqueamos aquí.
            pass

        # 3) Limpieza opcional de observación
        if self.observacion:
            self.observacion = self.observacion.strip()
            if len(self.observacion) > 255:
                raise ValidationError("La observación no puede superar 255 caracteres.")

    def save(self, *args, **kwargs):
        # Asegura validaciones de modelo incluso si se usa .create() o .save() directo
        self.full_clean()
        return super().save(*args, **kwargs)

    class Meta:
        # Unicidad por estudiante+fecha
        constraints = [
            models.UniqueConstraint(
                fields=["estudiante", "fecha"],
                name="uq_asistencia_dia",
            ),
        ]
        # Índices útiles
        indexes = [
            models.Index(fields=["fecha"]),
            models.Index(fields=["estudiante", "fecha"]),
        ]
        ordering = ["-fecha", "estudiante_id"]
        verbose_name = "asistencia"
        verbose_name_plural = "asistencias"

    def __str__(self):
        return f"{self.estudiante} - {self.fecha} ({self.estado})"
