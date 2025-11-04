# apps/citaciones/views/aprobacion.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.timezone import now
from django.db import transaction
from django import forms

from apps.citaciones.models.citacion import Citacion
from apps.citaciones.models.queue import QueueItem
from apps.citaciones.services.queue_service import sugerir_slot_por_mm1
from apps.citaciones.ws import push_citacion_padre
from apps.cuentas.decorators import role_required  # ya lo tienes en tu proyecto

class EditarCitacionForm(forms.ModelForm):
    class Meta:
        model = Citacion
        fields = ["motivo_resumen", "fecha_citacion", "hora_citacion", "duracion_min"]
        widgets = {
            "fecha_citacion": forms.DateInput(attrs={"type": "date"}),
            "hora_citacion": forms.TimeInput(attrs={"type": "time"}),
        }

@login_required
@role_required("director")
def pendientes(request):
    qs = (Citacion.objects
          .select_related("estudiante")
          .filter(estado=Citacion.Estado.ABIERTA)
          .order_by("-creado_en"))
    # Sugerencia M/M/1 por cada ítem (no persiste)
    sugerencias = {}
    for c in qs:
        ests, dt_sug = sugerir_slot_por_mm1()
        sugerencias[c.id] = dict(rho=ests["rho"], Wq=ests["Wq"], sugerido=dt_sug)
    return render(request, "citaciones/pendientes.html", {"citaciones": qs, "sugerencias": sugerencias})

@login_required
@role_required("director")
@transaction.atomic
def aprobar(request, pk):
    cit = get_object_or_404(Citacion, pk=pk, estado=Citacion.Estado.ABIERTA)

    # Recalcular sugerencia final al momento de aprobar
    ests, dt_sug = sugerir_slot_por_mm1()

    if not cit.fecha_citacion or not cit.hora_citacion:
        cit.fecha_citacion = dt_sug.date()
        cit.hora_citacion = dt_sug.time().replace(second=0, microsecond=0)

    if not cit.duracion_min:
        from apps.citaciones.models.config import AtencionConfig
        try:
            cfg = AtencionConfig.objects.latest("creado_en")
            cit.duracion_min = getattr(cfg, "duracion_por_defecto", 30)
        except Exception:
            cit.duracion_min = 30

    cit.estado = Citacion.Estado.AGENDADA
    cit.aprobado_por = request.user
    cit.aprobado_en = now()
    cit.save(update_fields=[
        "fecha_citacion","hora_citacion","duracion_min",
        "estado","aprobado_por","aprobado_en","actualizado_en"
    ])

    # Crear QueueItem (desde aquí cuenta para λ̂)
    QueueItem.objects.get_or_create(citacion=cit)

    # Notificar a padre por campana
    padre_id = getattr(cit.estudiante, "padre_id", None)
    if padre_id:
        push_citacion_padre(cit, padre_id)

    messages.success(request, f"Citación #{cit.id} aprobada y agendada.")
    return redirect("citaciones:pendientes")

@login_required
@role_required("director")
@transaction.atomic
def rechazar(request, pk):
    cit = get_object_or_404(Citacion, pk=pk, estado=Citacion.Estado.ABIERTA)
    cit.estado = Citacion.Estado.CANCELADA
    cit.save(update_fields=["estado","actualizado_en"])
    messages.info(request, f"Citación #{cit.id} rechazada.")
    return redirect("citaciones:pendientes")

@login_required
@role_required("director")
@transaction.atomic
def editar(request, pk):
    cit = get_object_or_404(Citacion, pk=pk, estado=Citacion.Estado.ABIERTA)
    if request.method == "POST":
        form = EditarCitacionForm(request.POST, instance=cit)
        if form.is_valid():
            form.save()
            messages.success(request, "Citación actualizada (pendiente de aprobación).")
            return redirect("citaciones:pendientes")
    else:
        form = EditarCitacionForm(instance=cit)

    ests, dt_sug = sugerir_slot_por_mm1()
    ctx = {"form": form, "citacion": cit, "sugerido": dt_sug, "rho": ests["rho"], "Wq": ests["Wq"]}
    return render(request, "citaciones/editar.html", ctx)
