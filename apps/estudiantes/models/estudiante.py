from django.db import models
from apps.cuentas.models import Usuario
from apps.cursos.models import Curso, Kardex


class Estudiante(models.Model):
    kardex = models.ForeignKey(Kardex, on_delete=models.RESTRICT, related_name="estudiantes")
    # ⬇️ Ahora puede quedar sin curso (no bloquea el borrado del curso)
    curso = models.ForeignKey(Curso, null=True, blank=True, on_delete=models.SET_NULL, related_name="estudiantes")
    padre = models.ForeignKey(Usuario, on_delete=models.RESTRICT, related_name="hijos")

    ci = models.CharField("CI", max_length=40, unique=True, null=True, blank=True)
    nombres = models.CharField(max_length=120)
    apellidos = models.CharField(max_length=120)
    fecha_nac = models.DateField(null=True, blank=True)

    class Sexo(models.TextChoices):
        M = "M", "Masculino"
        F = "F", "Femenino"

    sexo = models.CharField(max_length=1, choices=Sexo.choices, null=True, blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "estudiante"
        verbose_name_plural = "estudiantes"

    def __str__(self):
        return f"{self.apellidos}, {self.nombres}"
