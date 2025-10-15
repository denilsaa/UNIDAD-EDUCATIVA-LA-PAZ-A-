# En cuentas/forms.py

from django import forms
from .models import Usuario

class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['ci', 'nombres', 'apellidos', 'email', 'telefono', 'rol', 'is_activo']
    
    def clean_contraseña(self):
        """Si necesitas agregar alguna validación específica para la contraseña"""
        return self.cleaned_data.get('contraseña')
