# apps/estudiantes/forms/kardex_registro_form.py
from datetime import date, time
from calendar import monthrange
from django import forms
from django.utils.timezone import localdate

from apps.estudiantes.models.kardex_registro import KardexRegistro
from apps.estudiantes.models.kardex_item import KardexItem


class KardexRegistroForm(forms.ModelForm):
    class Meta:
        model = KardexRegistro
        fields = ["fecha", "hora", "kardex_item", "observacion", "sello_maestro"]
        labels = {
            "fecha": "Fecha",
            "hora": "Hora",
            "kardex_item": "Ítem del Kárdex",
            "observacion": "Observación",
            "sello_maestro": "Sello del maestro",
        }
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "hora": forms.TimeInput(attrs={"type": "time"}),
            "observacion": forms.TextInput(attrs={"placeholder": "Detalle breve"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Orden más cómodo para buscar Ítems
        self.fields["kardex_item"].queryset = KardexItem.objects.order_by("area", "descripcion")

        # ==== límites dinámicos ====
        hoy = localdate()
        last_day = monthrange(hoy.year, hoy.month)[1]
        first_of_month = date(hoy.year, hoy.month, 1)
        last_of_month = date(hoy.year, hoy.month, last_day)

        # Fecha: solo mes vigente
        self.fields["fecha"].widget.attrs.update({
            "min": first_of_month.isoformat(),
            "max": last_of_month.isoformat(),
        })

        # Hora: 07:00–14:00 cada 30 min
        self.fields["hora"].widget.attrs.update({
            "min": time(7, 0).strftime("%H:%M"),
            "max": time(14, 0).strftime("%H:%M"),
            "step": "1800",  # 1800s = 30 min
        })

    # Validaciones por si alguien fuerza el HTML
    def clean_fecha(self):
        f = self.cleaned_data.get("fecha")
        if not f:
            return f
        hoy = localdate()
        last_day = monthrange(hoy.year, hoy.month)[1]
        if not (date(hoy.year, hoy.month, 1) <= f <= date(hoy.year, hoy.month, last_day)):
            raise forms.ValidationError("Solo se permiten fechas del mes actual.")
        return f

    def clean_hora(self):
        h = self.cleaned_data.get("hora")
        if not h:
            return h
        if not (time(7, 0) <= h <= time(14, 0)):
            raise forms.ValidationError("La hora debe estar entre 07:00 y 14:00.")
        # fuerza múltiplos de 30 min
        if h.minute % 30 != 0 or h.second != 0:
            raise forms.ValidationError("La hora debe ir en intervalos de 30 minutos (00 o 30).")
        return h
