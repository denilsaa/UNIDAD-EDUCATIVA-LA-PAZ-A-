from django.db import models
from apps.estudiantes.models import Estudiante
from apps.cuentas.models import Usuario

class Citacion(models.Model):
    class Categoria(models.TextChoices):
        ASISTENCIA="ASISTENCIA"; CONDUCTA="CONDUCTA"; ACADEMICO="ACADEMICO"
    class Estado(models.TextChoices):
        ABIERTA="ABIERTA"; NOTIFICADA="NOTIFICADA"; AGENDADA="AGENDADA"
        ATENDIDA="ATENDIDA"; CERRADA="CERRADA"; CANCELADA="CANCELADA"

    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name="citaciones")
    creador = models.ForeignKey(Usuario, on_delete=models.RESTRICT, related_name="citaciones_creadas")
    categoria = models.CharField(max_length=12, choices=Categoria.choices)
    severidad = models.PositiveSmallIntegerField(default=1)  # se eleva al máximo de sus motivos
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.ABIERTA)

    fecha_citacion = models.DateField(null=True, blank=True)
    hora_citacion = models.TimeField(null=True, blank=True)

    # banderas opcionales
    flag_falta = models.BooleanField(default=False)
    flag_atraso = models.BooleanField(default=False)
    flag_no_tarea = models.BooleanField(default=False)

    puntaje_motivos = models.IntegerField(default=0)
    recurrencia_30d = models.IntegerField(default=0)
    impulso_manual = models.IntegerField(default=0)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_objetivo = models.DateTimeField(null=True, blank=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "citación"
        verbose_name_plural = "citaciones"

    def __str__(self):
        return f"Citación {self.id} — {self.estudiante}"
