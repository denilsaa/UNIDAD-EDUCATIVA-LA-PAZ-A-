# apps/estudiantes/forms.py
from django import forms

from apps.estudiantes.models.estudiante import Estudiante
from apps.cuentas.models.usuario import Usuario
from apps.cursos.models.curso import Curso

# Centinela (debe coincidir con lo usado en vistas de Curso)
SENT_NIVEL = "SIN"
SENT_PARALELO = "—"


class EstudianteForm(forms.ModelForm):
    padre = forms.ModelChoiceField(
        queryset=Usuario.objects.none(),
        label="Padre/Madre/Tutor",
        required=True,
    )

    class Meta:
        model = Estudiante
        fields = ["nombres", "apellidos", "ci", "curso", "padre"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1) Ocultar el curso centinela en el dropdown
        self.fields["curso"].queryset = (
            Curso.objects
            .exclude(nivel=SENT_NIVEL, paralelo=SENT_PARALELO)
            .order_by("nivel", "paralelo")
        )

        # 2) Si el estudiante YA está en el centinela, no mostrarlo seleccionado:
        #    dejamos el campo vacío para obligar a elegir un curso real.
        if self.instance and getattr(self.instance, "curso_id", None):
            c = self.instance.curso
            if c and c.nivel == SENT_NIVEL and c.paralelo == SENT_PARALELO:
                self.initial["curso"] = None
                self.fields["curso"].empty_label = "— Selecciona —"

        # 3) Lógica de padre de familia (tu original)
        qs_padres = (
            Usuario.objects
            .select_related("rol")
            .filter(rol__nombre__iexact="Padre de familia")
            .order_by("apellidos", "nombres")
        )
        self.fields["padre"].queryset = qs_padres
        self.fields["padre"].label_from_instance = (
            lambda u: f"{u.apellidos}, {u.nombres}" + (f" — {u.ci}" if u.ci else "")
        )

    def clean_padre(self):
        u = self.cleaned_data["padre"]
        if not u or not getattr(u, "rol", None) or (u.rol.nombre or "").lower() != "padre de familia":
            raise forms.ValidationError("Solo puede asignar usuarios con rol 'Padre de familia'.")
        return u
