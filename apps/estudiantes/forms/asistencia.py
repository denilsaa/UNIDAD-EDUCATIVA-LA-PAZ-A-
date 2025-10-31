from django import forms
from django.forms import formset_factory
from apps.estudiantes.models.asistencia import Asistencia
from apps.estudiantes.models.asistencia_config import AsistenciaCalendario, AsistenciaExclusion

class CalendarioAsistenciaForm(forms.ModelForm):
    class Meta:
        model = AsistenciaCalendario
        fields = ["fecha_inicio","fecha_fin","lunes","martes","miercoles","jueves","viernes"]
        widgets = {
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date"}),
        }
        labels = {
            "fecha_inicio": "Fecha inicio",
            "fecha_fin": "Fecha fin",
            "lunes": "Lunes",
            "martes": "Martes",
            "miercoles": "Miércoles",
            "jueves": "Jueves",
            "viernes": "Viernes",
        }

class ExclusionAsistenciaForm(forms.ModelForm):
    class Meta:
        model = AsistenciaExclusion
        fields = ["fecha"]
        widgets = {"fecha": forms.DateInput(attrs={"type": "date"})}

class RegistroFilaForm(forms.Form):
    estudiante_id = forms.IntegerField(widget=forms.HiddenInput())
    nombres = forms.CharField(disabled=True, required=False)
    estado = forms.ChoiceField(choices=Asistencia.Estado.choices, widget=forms.RadioSelect)

def build_registro_formset(estudiantes):
    BaseFormSet = formset_factory(RegistroFilaForm, extra=0)
    initial = [{"estudiante_id": e.id, "nombres": f"{e.apellidos}, {e.nombres}"} for e in estudiantes]
    return BaseFormSet(initial=initial)
