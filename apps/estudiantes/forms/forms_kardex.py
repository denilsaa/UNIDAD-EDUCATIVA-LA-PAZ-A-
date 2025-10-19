from django import forms
from apps.estudiantes.models.kardex_registro import KardexRegistro

class KardexRegistroForm(forms.ModelForm):
    class Meta:
        model = KardexRegistro
        fields = ["fecha","hora","kardex_item","observacion","sello_maestro"]
