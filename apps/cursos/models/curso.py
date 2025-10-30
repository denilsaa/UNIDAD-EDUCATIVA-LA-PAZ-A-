from django.db import models
from apps.cuentas.models import Usuario


class Curso(models.Model):
    nivel = models.CharField(max_length=40)
    paralelo = models.CharField(max_length=10)

    # ⬇️ Ahora el curso puede quedar sin regente (no bloquea al borrar un regente)
    regente = models.ForeignKey(
        Usuario,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cursos_regente",
    )

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["nivel", "paralelo"], name="uq_curso_np"),
        ]
        verbose_name = "curso"
        verbose_name_plural = "cursos"

    def __str__(self):
        return f"{self.nivel} {self.paralelo}"
