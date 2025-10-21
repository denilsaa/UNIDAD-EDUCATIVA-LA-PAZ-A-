from django import forms
from apps.cuentas.models import Usuario
from django.core.exceptions import ValidationError
import re

class UsuarioCreateForm(forms.ModelForm):
    nombres = forms.CharField(max_length=100)
    apellidos = forms.CharField(max_length=100)
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput)

    class Meta:
        model = Usuario
        fields = ["ci", "nombres", "apellidos", "email", "telefono", "rol", "is_activo"]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer que is_activo esté siempre True y no se muestre
        self.fields['is_activo'].initial = True
        self.fields['is_activo'].widget = forms.HiddenInput()
    def clean_ci(self):
        ci = self.cleaned_data.get("ci")
        
        if not ci.isdigit():
            raise forms.ValidationError("El CI solo debe contener números.")
        
        if len(ci) < 6 or len(ci) > 8:
            raise forms.ValidationError("El CI debe tener entre 6 y 8 números.")
        
        if Usuario.objects.filter(ci=ci).exists():
            raise forms.ValidationError("Este CI ya está registrado.")
        
        return ci
    def clean_nombres(self):
        nombres = self.cleaned_data.get("nombres", "").strip()

        # No puede estar vacío
        if not nombres:
            raise forms.ValidationError("El campo Nombres es obligatorio.")

        # Solo letras y espacios
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$', nombres):
            raise forms.ValidationError("Solo se permiten letras y espacios.")

        # Quitar espacios múltiples y validar estructura
        palabras = [p for p in nombres.split(" ") if p]  # Eliminar dobles espacios

        # Mínimo 1 palabra, máximo 3
        if len(palabras) < 1 or len(palabras) > 3:
            raise forms.ValidationError("Debes ingresar entre 1 y 3 palabras.")

        # Cada palabra debe tener al menos 3 letras
        for palabra in palabras:
            if len(palabra) < 3:
                raise forms.ValidationError("Cada palabra debe tener al menos 3 letras.")

        # Verificar que no haya espacios al inicio o final
        if nombres != nombres.strip():
            raise forms.ValidationError("No se permiten espacios al inicio o al final.")

        # Reconstruir el valor limpio (sin dobles espacios)
        nombres_limpios = " ".join(palabras)
        return nombres_limpios
    
    def clean_apellidos(self):
        apellidos = self.cleaned_data['apellidos'].strip()

        # Validar solo letras y espacios
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$', apellidos):
            raise ValidationError("Solo se permiten letras y espacios.")

        # Dividir en palabras
        palabras = apellidos.split()

        # Mínimo 1 palabra, máximo 2
        if len(palabras) < 1 or len(palabras) > 2:
            raise ValidationError("Debes ingresar uno o dos apellidos.")

        # Cada palabra debe tener al menos 3 letras
        if any(len(p) < 3 for p in palabras):
            raise ValidationError("Cada apellido debe tener al menos 3 letras.")

        return apellidos
    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        
        # Campo opcional
        if email == "":
            return email
        
        # Validar formato general de email
        email_regex = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            raise ValidationError("Correo inválido. Debe tener formato ejemplo@gmail.com")
        
        # limitamos solo a Gmail????
        # if not email.lower().endswith("@gmail.com"):
        #     raise ValidationError("Solo se permiten correos @gmail.com")
        
        return email
    # Dentro de tu UsuarioCreateForm o UsuarioUpdateForm
    def clean_telefono(self):
        telefono = self.cleaned_data.get("telefono", "").strip()

        if not telefono:
            raise ValidationError("El teléfono es obligatorio.")

        if not telefono.isdigit():
            raise ValidationError("El teléfono solo debe contener números.")

        if len(telefono) != 8:
            raise ValidationError("El teléfono debe tener exactamente 8 números.")

        if telefono[0] not in ("6", "7"):
            raise ValidationError("El teléfono debe empezar con 6 o 7.")

        return telefono
    # Dentro de tu UsuarioCreateForm o UsuarioUpdateForm
    def clean_rol(self):
        rol = self.cleaned_data.get("rol")
        if not rol:
            raise ValidationError("Debes seleccionar un rol.")
        return rol

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")

        if not p1 or not p2 or p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data["password1"])
        if commit:
            usuario.save()
        return usuario


class UsuarioUpdateForm(forms.ModelForm):
    # Campos opcionales para cambiar contraseña
    new_password1 = forms.CharField(label="Nueva contraseña", widget=forms.PasswordInput, required=False)
    new_password2 = forms.CharField(label="Confirmar nueva contraseña", widget=forms.PasswordInput, required=False)

    class Meta:
        model = Usuario
        fields = ["ci", "nombres", "apellidos", "email", "telefono", "rol", "is_activo"]

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password1")
        p2 = cleaned.get("new_password2")
        if (p1 or p2) and p1 != p2:
            raise forms.ValidationError("Las nuevas contraseñas no coinciden.")
        ci = cleaned.get("ci")
        email = cleaned.get("email")
        if not ci and not email:
            raise forms.ValidationError("Debes mantener CI o Email (al menos uno).")
        return cleaned

    def save(self, commit=True):
        usuario = super().save(commit=False)
        p1 = self.cleaned_data.get("new_password1")
        if p1:  # si el director decidió cambiar la contraseña
            usuario.set_password(p1)
        if commit:
            usuario.save()
        return usuario
