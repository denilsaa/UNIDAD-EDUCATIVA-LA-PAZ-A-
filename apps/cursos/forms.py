from django import forms
from apps.cursos.models import Curso
from apps.cuentas.models import Usuario

class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ["nivel", "paralelo", "regente"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # SOLO usuarios cuyo rol.nombre sea "Regente" (sin importar mayúsculas)
        # y que estén activos
        self.fields["regente"].queryset = (
            Usuario.objects
            .filter(rol__nombre__iexact="Regente", is_activo=True)
            .order_by("apellidos", "nombres")
        )

        # Opcional: cómo se muestra cada opción en el <select>
        # (Apellido, Nombre, CI si quieres)
        self.fields["regente"].label_from_instance = (
            lambda u: f"{u.apellidos}, {u.nombres}"
        )
