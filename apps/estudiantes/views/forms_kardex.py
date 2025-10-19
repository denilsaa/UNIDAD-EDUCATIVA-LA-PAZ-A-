from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils.timezone import now

from apps.estudiantes.models.estudiante import Estudiante
from apps.estudiantes.models.kardex_registro import KardexRegistro
from apps.estudiantes.models.kardex_item import KardexItem

# 🔒 roles
from apps.cuentas.roles import es_director, es_regente, es_secretaria, es_padre


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
@login_required
def kardex_registro_nuevo(request, estudiante_id: int):
    """
    Crear un registro (fila) del kárdex para un estudiante.
    Autorización:
      - Padre: NO puede crear.
      - Regente: solo si el estudiante pertenece a su curso.
      - Director/Secretaría: permitido.
    """
    estudiante = get_object_or_404(Estudiante, pk=estudiante_id)

    # 🔒 Autorización
    if es_padre(request.user):
        return render(request, "403.html", status=403)
    elif es_regente(request.user):
        if getattr(estudiante.curso, "regente_id", None) != request.user.id:
            return render(request, "403.html", status=403)
    elif not (es_director(request.user) or es_secretaria(request.user)):
        return render(request, "403.html", status=403)

    if request.method == "POST":
        form = KardexRegistroForm(request.POST)
        if form.is_valid():
            reg = form.save(commit=False)
            reg.estudiante = estudiante
            reg.save()
            messages.success(request, "Registro de kárdex añadido.")
            return redirect(reverse("estudiantes:kardex_listar", args=[estudiante.pk]))
        messages.error(request, "Por favor corrija los errores del formulario.")
    else:
        form = KardexRegistroForm(initial={"fecha": now().date()})

    return render(request, "kardex/registro_formulario.html", {"form": form, "estudiante": estudiante})


@login_required
def kardex_registro_listar(request, estudiante_id: int):
    """
    Muestra la planilla estilo papel: cabecera y grilla SER / SABER / HACER / DECIDIR.
    Autorización:
      - Padre: solo si el estudiante es su hijo.
      - Regente: solo si es regente del curso del estudiante.
      - Director/Secretaría: permitido.
    """
    estudiante = get_object_or_404(Estudiante, pk=estudiante_id)

    # 🔒 Autorización
    if es_padre(request.user):
        if getattr(estudiante, "padre_id", None) != request.user.id:
            return render(request, "403.html", status=403)
    elif es_regente(request.user):
        if getattr(estudiante.curso, "regente_id", None) != request.user.id:
            return render(request, "403.html", status=403)
    elif not (es_director(request.user) or es_secretaria(request.user)):
        return render(request, "403.html", status=403)

    # Columnas por área (orden fijo por ID para alinear filas)
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
