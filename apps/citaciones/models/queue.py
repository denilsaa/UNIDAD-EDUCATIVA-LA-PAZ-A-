# apps/citaciones/models/queue.py
from django.db import models
from django.utils.timezone import now
from .citacion import Citacion


class QueueItem(models.Model):
    class Estado(models.TextChoices):
        EN_COLA = "EN_COLA", "En cola"
        EN_SERVICIO = "EN_SERVICIO", "En servicio"
        ATENDIDA = "ATENDIDA", "Atendida"
        FALLIDA = "FALLIDA", "Fallida"

    citacion = models.OneToOneField(
        Citacion, on_delete=models.CASCADE, related_name="queue_item", verbose_name="Citación"
    )
    estado = models.CharField("Estado en cola", max_length=12, choices=Estado.choices, default=Estado.EN_COLA)

    llegada_en = models.DateTimeField("Llegó a la cola", auto_now_add=True)
    inicio_servicio_en = models.DateTimeField("Inicio de atención", null=True, blank=True)
    fin_servicio_en = models.DateTimeField("Fin de atención", null=True, blank=True)

    creado_en = models.DateTimeField("Creado en", auto_now_add=True)
    actualizado_en = models.DateTimeField("Actualizado en", auto_now=True)

    class Meta:
        ordering = ["llegada_en"]
        verbose_name = "ítem de cola"
        verbose_name_plural = "ítems de cola"

    def __str__(self):
        return f"{self.citacion} · {self.estado}"

    # Helpers para el worker
    def start_service(self, cuando=None):
        self.estado = self.Estado.EN_SERVICIO
        self.inicio_servicio_en = cuando or now()
        self.save(update_fields=["estado", "inicio_servicio_en", "actualizado_en"])

    def finish_service(self, cuando=None, ok=True):
        self.estado = self.Estado.ATENDIDA if ok else self.Estado.FALLIDA
        self.fin_servicio_en = cuando or now()
        self.save(update_fields=["estado", "fin_servicio_en", "actualizado_en"])
