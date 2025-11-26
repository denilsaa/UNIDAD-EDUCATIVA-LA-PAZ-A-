from django.db import models
from django.utils import timezone

from apps.cuentas.models import Usuario
from apps.estudiantes.models import Estudiante


class StudentLog(models.Model):
    class Accion(models.TextChoices):
        CREAR = "CREAR", "Creación"
        EDITAR = "EDITAR", "Modificación"
        ELIMINAR = "ELIMINAR", "Eliminación"

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs_estudiantes",
        help_text="Usuario que realizó la acción",
    )

    # FK al estudiante (puede quedar en NULL si se elimina)
    estudiante = models.ForeignKey(
        Estudiante,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs_auditoria",
        help_text="Estudiante sobre el que se realizó la acción",
    )

    # Copia del nombre/datos del estudiante para que NO se pierdan al borrar
    estudiante_nombre = models.CharField(
        max_length=255,
        blank=True,
        help_text="Nombre del estudiante en el momento de la acción",
    )

    accion = models.CharField(
        max_length=15,
        choices=Accion.choices,
    )
    descripcion = models.TextField(blank=True)

    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    creado_en = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "auditoria_studentlog"
        ordering = ["-creado_en"]

    def __str__(self):
        usuario = self.usuario or "Usuario desconocido"
        est = self.estudiante_nombre or "Estudiante desconocido"
        return f"[{self.get_accion_display()}] {usuario} -> {est} ({self.creado_en})"
