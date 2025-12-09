# apps/citaciones/forms.py
from datetime import time

from django import forms
from django.core.exceptions import ValidationError

from apps.citaciones.models.citacion import Citacion


class CitacionEditForm(forms.ModelForm):
    """
    Formulario para editar citaciones desde la bandeja de pendientes.

    Reglas:
      - Solo días Lunes–Viernes.
      - Hora entre 08:00 y 12:00.
      - Duración solo 15, 30, 45 o 60 minutos.
      - No se permite otra citación (ABIERTA / AGENDADA / NOTIFICADA)
        con la misma fecha y hora.
    """

    DUR_CHOICES = (
        (15, "15"),
        (30, "30"),
        (45, "45"),
        (60, "60"),
    )

    duracion_min = forms.TypedChoiceField(
        label="Duración (minutos)",
        choices=DUR_CHOICES,
        coerce=int,
        empty_value=None,
        help_text="15, 30, 45 o 60. Se usa para agenda y métricas.",
    )

    class Meta:
        model = Citacion
        fields = ["fecha_citacion", "hora_citacion", "duracion_min"]
        widgets = {
            "fecha_citacion": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                    "placeholder": "dd/mm/aaaa",
                }
            ),
            "hora_citacion": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "form-control",
                    "placeholder": "--:--",
                }
            ),
        }
        labels = {
            "fecha_citacion": "Fecha de citación",
            "hora_citacion": "Hora de citación",
        }

    # ======== Validaciones por campo ========

    def clean_fecha_citacion(self):
        fecha = self.cleaned_data.get("fecha_citacion")
        if not fecha:
            raise ValidationError("Debes seleccionar una fecha de citación.")

        # 0 = lunes, 6 = domingo
        if fecha.weekday() >= 5:  # sábado o domingo
            raise ValidationError("La citación solo puede agendarse de lunes a viernes.")

        return fecha

    def clean_hora_citacion(self):
        hora = self.cleaned_data.get("hora_citacion")
        if not hora:
            raise ValidationError("Debes seleccionar una hora de citación.")

        inicio = time(8, 0)
        fin = time(12, 0)  # si quieres que el último inicio sea 11:45, lo ajustamos luego

        if not (inicio <= hora <= fin):
            raise ValidationError("La hora debe estar entre 08:00 y 12:00.")

        return hora

    def clean_duracion_min(self):
        dur = self.cleaned_data.get("duracion_min")
        if dur not in (15, 30, 45, 60):
            raise ValidationError("La duración debe ser 15, 30, 45 o 60 minutos.")
        return dur

    # ======== Validación cruzada (fecha + hora únicas) ========

    def clean(self):
        cleaned = super().clean()
        fecha = cleaned.get("fecha_citacion")
        hora = cleaned.get("hora_citacion")

        # Solo validamos colisión si ambos están presentes
        if not fecha or not hora:
            return cleaned

        qs = Citacion.objects.filter(
            fecha_citacion=fecha,
            hora_citacion=hora,
            estado__in=[
                Citacion.Estado.ABIERTA,
                Citacion.Estado.AGENDADA,
                Citacion.Estado.NOTIFICADA,
            ],
        )

        # excluir la propia citación si se está editando
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError(
                "Ya existe una citación programada para esa fecha y hora "
                "(incluye pendientes y aprobadas)."
            )

        return cleaned
