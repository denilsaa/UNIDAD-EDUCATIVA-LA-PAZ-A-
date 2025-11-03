from django.db import models
from django.core.exceptions import ValidationError

class AsistenciaCalendario(models.Model):
    """
    Definido por el Director: rango de fechas y qué días hábiles (L–V) cuentan.
    Suele haber UNO activo a la vez.
    """
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    # Días hábiles (solo L–V)
    lunes = models.BooleanField(default=True)
    martes = models.BooleanField(default=True)
    miercoles = models.BooleanField(default=True)
    jueves = models.BooleanField(default=True)
    viernes = models.BooleanField(default=True)

    # Gestión
    activo = models.BooleanField(default=True)
    creado_por = models.ForeignKey(
        "cuentas.Usuario", on_delete=models.PROTECT, related_name="asis_cal_creados"
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-activo", "-fecha_inicio"]
        verbose_name = "calendario de asistencia"
        verbose_name_plural = "calendarios de asistencia"

    # --- Reglas de negocio básicas ---
    def clean(self):
        if self.fecha_fin < self.fecha_inicio:
            raise ValidationError("La fecha fin no puede ser menor a la fecha inicio.")
        if not any([self.lunes, self.martes, self.miercoles, self.jueves, self.viernes]):
            raise ValidationError("Habilita al menos un día entre lunes y viernes.")

    def save(self, *args, **kwargs):
        """
        Si este calendario queda activo, desactiva los demás.
        (Garantiza que normalmente haya uno solo 'activo')
        """
        super().save(*args, **kwargs)
        if self.activo:
            AsistenciaCalendario.objects.exclude(pk=self.pk).update(activo=False)

    def __str__(self):
        estado = "Activo" if self.activo else "Inactivo"
        return f"{self.fecha_inicio} → {self.fecha_fin} ({estado})"

    # --- Utilidad para validar fechas ---
    def admite_fecha(self, fecha):
        """True si fecha está en rango, es L–V habilitado y NO está excluida."""
        if not (self.fecha_inicio <= fecha <= self.fecha_fin):
            return False
        dow = fecha.weekday()  # 0=lu .. 6=do
        dia_ok = {
            0: self.lunes,
            1: self.martes,
            2: self.miercoles,
            3: self.jueves,
            4: self.viernes,
        }.get(dow, False)
        if not dia_ok:
            return False
        if self.exclusiones.filter(fecha=fecha).exists():
            return False
        return True


class AsistenciaExclusion(models.Model):
    """
    Días marcados por el Director como 'no se llama lista' dentro del rango.
    """
    calendario = models.ForeignKey(
        AsistenciaCalendario, on_delete=models.CASCADE, related_name="exclusiones"
    )
    fecha = models.DateField()

    class Meta:
        unique_together = [("calendario", "fecha")]
        ordering = ["fecha"]
        verbose_name = "exclusión de asistencia"
        verbose_name_plural = "exclusiones de asistencia"

    def clean(self):
        # Nota: clean se usa con commit=False en la vista y ya se setea calendario antes de full_clean()
        if not (self.calendario.fecha_inicio <= self.fecha <= self.calendario.fecha_fin):
            raise ValidationError("La fecha excluida debe estar dentro del rango del calendario.")

    def __str__(self):
        cal_id = getattr(self, "calendario_id", None)
        return f"{self.fecha} (sin lista) · cal:{cal_id or '—'}"
