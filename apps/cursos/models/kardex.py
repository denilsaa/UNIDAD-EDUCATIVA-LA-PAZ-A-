from django.db import models
from .curso import Curso

class Kardex(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.RESTRICT, null=True, blank=True)
    anio = models.PositiveSmallIntegerField()
    trimestre = models.PositiveSmallIntegerField()   # 1..3/4
    observacion = models.CharField(max_length=255, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["curso", "anio", "trimestre"])]
        verbose_name = "kárdex"
        verbose_name_plural = "kárdex"

    def __str__(self):
        return f"Kárdex {self.anio}-T{self.trimestre}"
