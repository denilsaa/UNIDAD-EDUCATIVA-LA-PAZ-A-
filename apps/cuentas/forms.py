from django import forms
from apps.cuentas.models import Usuario

class UsuarioCreateForm(forms.ModelForm):
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput)

    class Meta:
        model = Usuario
        fields = ["ci", "nombres", "apellidos", "email", "telefono", "rol", "is_activo"]

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")

        # Verificar si las contraseñas coinciden
        if not p1 or not p2 or p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned

    def save(self, commit=True):
        usuario = super().save(commit=False)
        # Guardar el hash de la contraseña en password_hash
        usuario.set_password(self.cleaned_data["password1"])  # Esto genera el hash
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
