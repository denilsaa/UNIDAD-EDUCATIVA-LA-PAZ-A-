# apps/cursos/forms.py
from django import forms
from apps.cursos.models import Curso

class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ["nivel", "paralelo", "regente"]
        widgets = {
            "nivel": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej. Secundaria 3°"}),
            "paralelo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej. A"}),
            "regente": forms.Select(attrs={"class": "form-select"}),
        }
