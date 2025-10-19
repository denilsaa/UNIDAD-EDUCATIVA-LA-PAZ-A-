# apps/estudiantes/views/forms_kardex.py
from django import forms
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.timezone import now

from apps.estudiantes.models.estudiante import Estudiante
from apps.estudiantes.models.kardex_registro import KardexRegistro
from apps.estudiantes.models.kardex_item import KardexItem

# ---------- FORMULARIO ----------
class KardexRegistroForm(forms.ModelForm):
    class Meta:
        model = KardexRegistro
        fields = ["fecha", "hora", "kardex_item", "observacion", "sello_maestro"]
        labels = {
            "fecha": "Fecha",
            "hora": "Hora",
            "kardex_item": "Ítem del Kárdex",
            "observacion": "Observación",
            "sello_maestro": "Sello del maestro",
        }
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "hora": forms.TimeInput(attrs={"type": "time"}),
            "observacion": forms.TextInput(attrs={"placeholder": "Detalle breve"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar por área y descripción para que sea más fácil encontrar el ítem
        self.fields["kardex_item"].queryset = KardexItem.objects.order_by("area", "descripcion")

# ---------- VISTAS ----------
def kardex_registro_nuevo(request, estudiante_id: int):
    """Crear un registro (fila) del kárdex para un estudiante."""
    estudiante = get_object_or_404(Estudiante, pk=estudiante_id)

    if request.method == "POST":
        form = KardexRegistroForm(request.POST)
        if form.is_valid():
            reg = form.save(commit=False)
            reg.estudiante = estudiante
            reg.save()
            messages.success(request, "Registro de kárdex añadido.")
            return redirect(reverse("estudiantes:kardex_listar", args=[estudiante.pk]))
    else:
        form = KardexRegistroForm(initial={"fecha": now().date()})

    return render(request, "kardex/registro_formulario.html", {"form": form, "estudiante": estudiante})


def kardex_registro_listar(request, estudiante_id: int):
    """
    Muestra la planilla estilo papel: cabecera y grilla SER / SABER / HACER / DECIDIR.
    Cada registro ocupa una fila y se marca con ✔ en la columna del ítem elegido.
    """
    estudiante = get_object_or_404(Estudiante, pk=estudiante_id)

    # ⚠️ Usar 'area' (no 'dimension')
    ser_cols     = list(KardexItem.objects.filter(area="SER").order_by("id"))
    saber_cols   = list(KardexItem.objects.filter(area="SABER").order_by("id"))
    hacer_cols   = list(KardexItem.objects.filter(area="HACER").order_by("id"))
    decidir_cols = list(KardexItem.objects.filter(area="DECIDIR").order_by("id"))

    registros = (
        KardexRegistro.objects
        .filter(estudiante=estudiante)
        .select_related("kardex_item")
        .order_by("-fecha", "-hora", "-id")
    )

    filas_max = 15
    filas = list(registros[:filas_max])

    contexto = {
        "estudiante": estudiante,
        "ser_cols": ser_cols,
        "saber_cols": saber_cols,
        "hacer_cols": hacer_cols,
        "decidir_cols": decidir_cols,
        "filas": filas,
        "filas_max": filas_max,
    }
    return render(request, "kardex/registro_lista.html", contexto)
