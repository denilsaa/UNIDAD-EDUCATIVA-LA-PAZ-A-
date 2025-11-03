# apps/citaciones/models/citacion.py
from django.db import models
from apps.estudiantes.models.estudiante import Estudiante
from apps.estudiantes.models.kardex_registro import KardexRegistro
from apps.cuentas.models import Usuario


class Citacion(models.Model):
    class Estado(models.TextChoices):
        ABIERTA = "ABIERTA", "Abierta (borrador)"
        AGENDADA = "AGENDADA", "Agendada"
        NOTIFICADA = "NOTIFICADA", "Notificada a padres/tutores"
        ATENDIDA = "ATENDIDA", "Atendida"
        CANCELADA = "CANCELADA", "Cancelada"

    # --- Relación base ---
    estudiante = models.ForeignKey(
        Estudiante,
        on_delete=models.RESTRICT,
        related_name="citaciones",
        verbose_name="Estudiante",
    )
    kardex_registro = models.OneToOneField(
        KardexRegistro,
        on_delete=models.RESTRICT,
        related_name="citacion_origen",
        verbose_name="Registro de Kárdex",
        null=True, blank=True,          # <-- AÑADE ESTO
    )


    # --- Motivo resumido (puedes tener además tu relación a motivos detallados) ---
    motivo_resumen = models.CharField(
        "Motivo (resumen)", max_length=160, blank=True, default=""
    )

    # --- Estado de la citación ---
    estado = models.CharField(
        "Estado", max_length=12, choices=Estado.choices, default=Estado.ABIERTA
    )

    # ============= NUEVO: aprobación + duración (añade ESTOS campos) =============
    duracion_min = models.PositiveSmallIntegerField(
        "Duración (minutos)", default=30,
        help_text="15, 30, 45 o 60. Se usa para agenda y métricas."
    )
    aprobado_por = models.ForeignKey(
        Usuario, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="citaciones_aprobadas", verbose_name="Aprobado por"
    )
    aprobado_en = models.DateTimeField("Aprobado en", null=True, blank=True)
    # ============================================================================

    # --- Agenda (si ya tienes campos de fecha/hora, mantenlos; si no, estos ayudan) ---
    fecha_citacion = models.DateField("Fecha de citación", null=True, blank=True)
    hora_citacion = models.TimeField("Hora de citación", null=True, blank=True)

    creado_en = models.DateTimeField("Creado en", auto_now_add=True)
    actualizado_en = models.DateTimeField("Actualizado en", auto_now=True)

    class Meta:
        verbose_name = "citación"
        verbose_name_plural = "citaciones"
        ordering = ["-creado_en"]

    def __str__(self):
        base = f"{self.estudiante} · {self.motivo_resumen or 'Citación'}"
        if self.fecha_citacion and self.hora_citacion:
            return f"{base} · {self.fecha_citacion:%d/%m} {self.hora_citacion:%H:%M}"
        return base
