from django.db import models

class SelladoTiempo(models.Model):
    """Mixin de timestamps."""
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="creado en")
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name="actualizado en")

    class Meta:
        abstract = True
