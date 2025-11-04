# apps/notificaciones/models/notificacion.py
from django.db import models
from django.utils.timezone import now
from apps.cuentas.models import Usuario
from apps.citaciones.models import Citacion

class Notificacion(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        ENVIADA   = "ENVIADA", "Enviada"
        LEIDA     = "LEIDA", "Leída"

    # === columnas reales de la tabla notificaciones_notificacion ===
    usuario_destino = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name="notificaciones",
        db_column="receptor_id", verbose_name="Usuario destino"
    )
    citacion = models.ForeignKey(
        Citacion, on_delete=models.CASCADE, related_name="notificaciones",
        null=True, blank=True, db_column="citacion_id", verbose_name="Citación relacionada"
    )
    titulo = models.CharField(max_length=120, db_column="titulo")
    cuerpo = models.TextField(blank=True, default="", db_column="mensaje")
    data = models.JSONField(null=True, blank=True, db_column="data")
    estado_entrega = models.CharField(
        max_length=10, choices=Estado.choices, default=Estado.PENDIENTE,
        db_column="estado_entrega"
    )
    enviada_en = models.DateTimeField(default=now, db_column="ts_creacion")
    entregada_en = models.DateTimeField(null=True, blank=True, db_column="ts_entrega")
    leida_en = models.DateTimeField(null=True, blank=True, db_column="ts_lectura")
    actualizado_en = models.DateTimeField(null=True, blank=True, db_column="actualizado_en")

    class Meta:
        db_table = "notificaciones_notificacion"
        managed = False
        ordering = ["-enviada_en"]

    def __str__(self):
        return f"{self.usuario_destino_id} · {self.titulo}"

    @property
    def leida(self) -> bool:
        return self.leida_en is not None
