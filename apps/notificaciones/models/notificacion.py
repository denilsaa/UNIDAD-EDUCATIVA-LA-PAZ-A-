# apps/notificaciones/models/notificacion.py
from django.db import models
from apps.cuentas.models import Usuario
from apps.citaciones.models import Citacion


class Notificacion(models.Model):
    class Canal(models.TextChoices):
        IN_APP = "in_app", "En la aplicación"

    usuario_destino = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name="notificaciones",
        verbose_name="Usuario destino"
    )
    citacion = models.ForeignKey(
        Citacion, on_delete=models.CASCADE, related_name="notificaciones",
        null=True, blank=True, verbose_name="Citación relacionada"
    )
    canal = models.CharField("Canal", max_length=16, choices=Canal.choices, default=Canal.IN_APP)
    titulo = models.CharField("Título", max_length=140)
    cuerpo = models.TextField("Cuerpo", blank=True, default="")
    leida = models.BooleanField("Leída", default=False)
    enviada_en = models.DateTimeField("Enviada en", auto_now_add=True)
    leida_en = models.DateTimeField("Leída en", null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["usuario_destino", "leida"]),
            models.Index(fields=["enviada_en"]),
        ]
        ordering = ["-enviada_en"]
        verbose_name = "notificación"
        verbose_name_plural = "notificaciones"

    def __str__(self):
        return f"{self.usuario_destino} · {self.titulo}"
