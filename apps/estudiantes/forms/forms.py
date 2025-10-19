from django import forms
from apps.estudiantes.models.estudiante import Estudiante
from apps.cuentas.models.usuario import Usuario

class EstudianteForm(forms.ModelForm):
    padre = forms.ModelChoiceField(
        queryset=Usuario.objects.none(),
        label="Padre/Madre/Tutor",
        required=True
    )

    class Meta:
        model = Estudiante
        fields = ["nombres", "apellidos", "ci", "curso", "padre"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Usuario.objects.select_related("rol").filter(rol__nombre__iexact="Padre de familia").order_by("apellidos","nombres")
        self.fields["padre"].queryset = qs
        self.fields["padre"].label_from_instance = lambda u: f"{u.apellidos}, {u.nombres}" + (f" — {u.ci}" if u.ci else "")

    def clean_padre(self):
        u = self.cleaned_data["padre"]
        if not u or not getattr(u, "rol", None) or (u.rol.nombre or "").lower() != "padre de familia":
            raise forms.ValidationError("Solo puede asignar usuarios con rol 'Padre de familia'.")
        return u
