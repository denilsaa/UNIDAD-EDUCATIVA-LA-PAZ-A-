from django.db import models
from .curso import Curso


class Kardex(models.Model):
    # ⬇️ Si borras el curso, el kardex queda sin curso (no bloquea)
    curso = models.ForeignKey(Curso, null=True, blank=True, on_delete=models.SET_NULL)
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
