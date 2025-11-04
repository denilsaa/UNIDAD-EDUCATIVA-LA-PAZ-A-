# apps/citaciones/views/bandeja.py
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date, parse_time

from apps.citaciones.models.citacion import Citacion
from apps.citaciones.services import queue_service
from apps.cuentas.roles import es_director
from django.shortcuts import get_object_or_404, redirect
from apps.citaciones.forms import CitacionEditForm
from apps.citaciones.services.metrics_service import metrics_payload

@login_required
@require_http_methods(["GET"])
def pendientes(request):
    if not es_director(request.user):
        return HttpResponseForbidden()
    qs = Citacion.objects.filter(estado=Citacion.Estado.ABIERTA).order_by("-creado_en")
    return render(request, "citaciones/pendientes.html", {"rows": qs})


@login_required
@require_POST
def aprobar(request, pk: int):
    if not es_director(request.user):
        return HttpResponseForbidden()
    c = queue_service.aprobar(pk, request.user)
    return JsonResponse({
        "ok": True,
        "id": c.id,
        "estado": c.estado,
        "fecha": c.fecha_citacion.isoformat() if c.fecha_citacion else None,
        "hora": c.hora_citacion.strftime("%H:%M") if c.hora_citacion else None,
    })


@login_required
@require_POST
def editar(request, pk: int):
    if not es_director(request.user):
        return HttpResponseForbidden()
    fecha = parse_date(request.POST.get("fecha"))
    hora = parse_time(request.POST.get("hora"))
    dur = request.POST.get("duracion_min")
    dur = int(dur) if dur else None
    c = queue_service.editar(pk, fecha, hora, dur, request.user)
    return JsonResponse({"ok": True, "id": c.id, "estado": c.estado})


@login_required
@require_POST
def rechazar(request, pk: int):
    if not es_director(request.user):
        return HttpResponseForbidden()
    c = queue_service.rechazar(pk, request.user)
    return JsonResponse({"ok": True, "id": c.id, "estado": c.estado})

@login_required
@require_http_methods(["GET", "POST"])
def editar_form(request, pk: int):
    if not es_director(request.user):
        return HttpResponseForbidden()
    c = get_object_or_404(Citacion, id=pk)

    if request.method == "POST":
        form = CitacionEditForm(request.POST, instance=c)
        if form.is_valid():
            form.save()
            return redirect("citaciones:pendientes")
    else:
        form = CitacionEditForm(instance=c)

    mm1 = metrics_payload()  # por si quieres pintar ρ/Wq/Ws en el lateral
    return render(request, "citaciones/editar.html", {
        "citacion": c,
        "form": form,
        "rho": mm1.get("rho"),
        "Wq": (mm1.get("Wq") or 0) * 60.0,  # a minutos si quieres
        "sugerido": None,  # podríamos calcular next_free_slot aquí si quieres sugerir
    })