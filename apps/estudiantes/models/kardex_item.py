from django.db import models

class KardexItem(models.Model):
    class Area(models.TextChoices):
        SER="SER"; SABER="SABER"; HACER="HACER"; DECIDIR="DECIDIR"
    class Sentido(models.TextChoices):
        NEGATIVO="NEGATIVO"; POSITIVO="POSITIVO"

    area = models.CharField(max_length=10, choices=Area.choices)
    descripcion = models.CharField(max_length=160)
    sentido = models.CharField(max_length=10, choices=Sentido.choices, default=Sentido.NEGATIVO)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["area","descripcion"], name="uq_kdx_item")]
        verbose_name = "ítem de kárdex"
        verbose_name_plural = "ítems de kárdex"

    def __str__(self):
        return f"[{self.area}] {self.descripcion}"
