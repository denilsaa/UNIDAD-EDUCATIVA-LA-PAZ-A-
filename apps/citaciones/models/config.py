# apps/citaciones/models/config.py
from django.db import models
from datetime import time


class AtencionConfig(models.Model):
    """
    Agenda de citaciones:
    - 08:00–12:00 por defecto
    - Slot de 15 min
    - Duración por defecto 30 min
    - Máximo de 7 días para agendar
    """
    hora_inicio = models.TimeField("Hora de inicio", default=time(8, 0))
    hora_fin = models.TimeField("Hora de fin", default=time(12, 0))
    minutos_por_slot = models.PositiveSmallIntegerField("Minutos por slot", default=15)
    duracion_por_defecto = models.PositiveSmallIntegerField("Duración por defecto (min)", default=30)
    max_dias = models.PositiveSmallIntegerField("Días máximos para agendar", default=7)

    creado_en = models.DateTimeField("Creado en", auto_now_add=True)
    actualizado_en = models.DateTimeField("Actualizado en", auto_now=True)

    class Meta:
        verbose_name = "configuración de atención"
        verbose_name_plural = "configuraciones de atención"

    def __str__(self):
        return f"{self.hora_inicio}-{self.hora_fin} · cada {self.minutos_por_slot}min · ≤{self.max_dias}d"


class ReglaTransversalConfig(models.Model):
    """
    Regla transversal: suma de pesos ≥ umbral en N días → crear citación abierta.
    Permite programar su entrada en vigor (ej.: próximo lunes 00:00).
    """
    habilitada = models.BooleanField("Habilitada", default=True)
    umbral = models.PositiveSmallIntegerField("Umbral de suma", default=35)
    ventana_dias = models.PositiveSmallIntegerField("Ventana (días)", default=14)

    programada = models.BooleanField("Programada", default=False)
    vigente_desde = models.DateTimeField("Vigente desde", null=True, blank=True)

    historial_json = models.TextField("Historial (JSON)", blank=True, default="[]")

    creado_en = models.DateTimeField("Creado en", auto_now_add=True)
    actualizado_en = models.DateTimeField("Actualizado en", auto_now=True)

    class Meta:
        verbose_name = "configuración de regla transversal"
        verbose_name_plural = "configuraciones de regla transversal"

    def __str__(self):
        onoff = "ON" if self.habilitada else "OFF"
        return f"Transversal {onoff} · umbral {self.umbral} · {self.ventana_dias} días"
