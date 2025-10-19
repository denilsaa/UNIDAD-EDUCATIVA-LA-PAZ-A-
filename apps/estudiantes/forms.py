from django import forms
from apps.estudiantes.models.estudiante import Estudiante
from apps.cuentas.models.usuario import Usuario

class EstudianteForm(forms.ModelForm):
    # Dejamos el queryset vacío y lo fijamos en __init__
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

        # FILTRO ESTRICTO: solo usuarios con rol "Padre de familia"
        qs = (Usuario.objects
              .select_related("rol")
              .filter(rol__nombre__iexact="Padre de familia")
              .order_by("apellidos", "nombres", "ci"))
        # Si también quieres solo activos, descomenta:
        # qs = qs.filter(is_activo=True)

        self.fields["padre"].queryset = qs

        # Cómo se muestra cada opción en el <select>
        self.fields["padre"].label_from_instance = (
            lambda u: f"{u.apellidos}, {u.nombres}" + (f" — {u.ci}" if u.ci else "")
        )

    def clean_padre(self):
        u = self.cleaned_data["padre"]
        # Validación servidor por si alguien intenta “forzar” otro rol
        if not u or not getattr(u, "rol", None) or (u.rol.nombre or "").lower() != "padre de familia":
            raise forms.ValidationError("Solo puede asignar usuarios con rol 'Padre de familia'.")
        return u
