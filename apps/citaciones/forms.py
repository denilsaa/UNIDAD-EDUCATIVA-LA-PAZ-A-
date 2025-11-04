# apps/citaciones/forms.py
from django import forms
from apps.citaciones.models.citacion import Citacion

class CitacionEditForm(forms.ModelForm):
    class Meta:
        model = Citacion
        fields = ["fecha_citacion", "hora_citacion", "duracion_min"]
        widgets = {
            "fecha_citacion": forms.DateInput(attrs={"type":"date"}),
            "hora_citacion": forms.TimeInput(attrs={"type":"time"}),
        }
