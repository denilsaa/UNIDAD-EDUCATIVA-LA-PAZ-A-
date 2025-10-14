from django.db import models
from .citacion import Citacion
from .motivo import MotivoCitacion

class CitacionMotivo(models.Model):
    citacion = models.ForeignKey(Citacion, on_delete=models.CASCADE, related_name="detalles_motivo")
    motivo = models.ForeignKey(MotivoCitacion, on_delete=models.RESTRICT)
    observacion = models.CharField(max_length=255, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["citacion", "motivo"], name="uq_cit_mot"),
        ]
        verbose_name = "detalle de motivo"
        verbose_name_plural = "detalles de motivos"

    def __str__(self):
        return f"{self.citacion_id} -> {self.motivo.codigo}"
