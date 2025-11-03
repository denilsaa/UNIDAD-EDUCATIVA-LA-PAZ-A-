from django.db import models

class KardexItem(models.Model):
    class Area(models.TextChoices):
        SER = "SER", "SER"
        SABER = "SABER", "SABER"
        HACER = "HACER", "HACER"
        DECIDIR = "DECIDIR", "DECIDIR"

    class Sentido(models.TextChoices):
        POSITIVO = "POSITIVO", "Positivo"
        NEGATIVO = "NEGATIVO", "Negativo"

    area = models.CharField("Área", max_length=16, choices=Area.choices)
    descripcion = models.CharField("Descripción", max_length=160)
    sentido = models.CharField("Sentido", max_length=16, choices=Sentido.choices, default=Sentido.NEGATIVO)

    # ===== nuevos campos =====
    peso = models.PositiveSmallIntegerField(
        "Peso (severidad)", default=10,
        help_text="Severidad base: p.ej., 5 (leve), 10 (mod.), 20 (import.), 35 (grave)."
    )
    ventana_dias = models.PositiveSmallIntegerField(
        "Ventana (días)", default=14,
        help_text="Período para contar recurrencias del mismo ítem."
    )
    umbral = models.PositiveSmallIntegerField(
        "Umbral (repeticiones)", default=0,
        help_text="Cantidad dentro de la ventana para disparar citación (0 = sin acumulación)."
    )
    directa = models.BooleanField(
        "Citación directa", default=False,
        help_text="Si es True, un solo evento crea citación (Abierta)."
    )
    activo = models.BooleanField("Activo", default=True)

    creado_en = models.DateTimeField("Creado en", auto_now_add=True)
    actualizado_en = models.DateTimeField("Actualizado en", auto_now=True)

    class Meta:
        # Mantén la unicidad original + el índice nuevo
        constraints = [models.UniqueConstraint(fields=["area", "descripcion"], name="uq_kdx_item")]
        indexes = [models.Index(fields=["area", "sentido", "activo"])]
        ordering = ["area", "descripcion"]
        verbose_name = "ítem de kárdex"
        verbose_name_plural = "ítems de kárdex"

    def __str__(self):
        return f"{self.area} · {self.descripcion}"
