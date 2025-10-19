# apps/estudiantes/forms/kardex_item.py
from django import forms
from apps.estudiantes.models.kardex_item import KardexItem

class KardexItemForm(forms.ModelForm):
    class Meta:
        model = KardexItem
        fields = ["area", "descripcion", "sentido"]
        widgets = {
            "descripcion": forms.TextInput(attrs={
                "maxlength": 160, "placeholder": "Descripción corta del ítem"
            }),
        }

    def clean_descripcion(self):
        txt = (self.cleaned_data.get("descripcion") or "").strip()
        txt = " ".join(txt.split())
        if not txt:
            raise forms.ValidationError("La descripción no puede estar vacía.")
        return txt
