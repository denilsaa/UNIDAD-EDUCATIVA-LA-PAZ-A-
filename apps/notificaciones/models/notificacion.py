from django.db import models
from apps.cuentas.models import Usuario
from apps.citaciones.models import Citacion

class Notificacion(models.Model):
    class EstadoEntrega(models.TextChoices):
        PENDIENTE="PENDIENTE"; ENTREGADA="ENTREGADA"; LEIDA="LEIDA"; ERROR="ERROR"

    citacion = models.ForeignKey(Citacion, on_delete=models.CASCADE, related_name="notificaciones")
    receptor = models.ForeignKey(Usuario, on_delete=models.RESTRICT, related_name="notificaciones")
    titulo = models.CharField(max_length=120)
    mensaje = models.TextField()
    data = models.JSONField(null=True, blank=True)
    estado_entrega = models.CharField(max_length=10, choices=EstadoEntrega.choices, default=EstadoEntrega.PENDIENTE)
    ts_creacion = models.DateTimeField(auto_now_add=True)
    ts_entrega = models.DateTimeField(null=True, blank=True)
    ts_lectura = models.DateTimeField(null=True, blank=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["receptor", "estado_entrega", "ts_creacion"]),
            models.Index(fields=["citacion"]),
        ]
        verbose_name = "notificación"
        verbose_name_plural = "notificaciones"

    def __str__(self):
        return f"Notif {self.id} a {self.receptor_id}"
