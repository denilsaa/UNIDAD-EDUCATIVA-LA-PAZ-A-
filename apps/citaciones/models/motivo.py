from django.db import models

class MotivoCitacion(models.Model):
    class Area(models.TextChoices):
        SER="SER"; SABER="SABER"; HACER="HACER"; DECIDIR="DECIDIR"

    codigo = models.SlugField(max_length=40, unique=True)
    area = models.CharField(max_length=7, choices=Area.choices)
    descripcion = models.CharField(max_length=200)
    severidad_default = models.PositiveSmallIntegerField()       # 1..4
    peso_prioridad_default = models.PositiveSmallIntegerField()  # peso para score
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "motivo de citación"
        verbose_name_plural = "motivos de citación"

    def __str__(self):
        return self.descripcion
