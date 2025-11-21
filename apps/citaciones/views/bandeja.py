# apps/citaciones/views/bandeja.py
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date, parse_time

from apps.citaciones.models.citacion import Citacion
from apps.citaciones.models.config import AtencionConfig
from apps.citaciones.services import queue_service
from apps.cuentas.roles import es_director
from django.shortcuts import get_object_or_404, redirect
from apps.citaciones.forms import CitacionEditForm
from apps.citaciones.services.metrics_service import metrics_payload

from apps.citaciones.services.agenda_service import suggest_free_slot
from apps.citaciones.services.metrics_service import metrics_payload

from apps.citaciones.services import queue_service
from apps.cuentas.roles import es_director

from datetime import datetime, timedelta
from django.utils.timezone import localdate
from django.utils.dateparse import parse_date
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseForbidden
from django.shortcuts import render

from apps.cuentas.roles import es_director
from apps.citaciones.models.citacion import Citacion


@login_required
@require_http_methods(["GET"])
def pendientes(request):
    if not es_director(request.user):
        return HttpResponseForbidden()

    # Ordenar por peso: mayor duración primero, luego por fecha de creación
    qs = (Citacion.objects
          .filter(estado=Citacion.Estado.ABIERTA)
          .order_by("-duracion_min", "-creado_en"))

    # Configuración de duración por defecto
    cfg = AtencionConfig.objects.first()
    dur_def = int(getattr(cfg, "duracion_por_defecto", 30) or 30)

    # Simular la cola M/M/1 para dar una ETA distinta a cada citación pendiente
    desde_sim = None
    for c in qs:
        try:
            dur = int(c.duracion_min or dur_def)
            if desde_sim is None:
                f, h = suggest_free_slot(duracion_min=dur, desde=None)
            else:
                f, h = suggest_free_slot(duracion_min=dur, desde=desde_sim)
            c.eta_fecha = f
            c.eta_hora = h
            # la siguiente citación en la simulación empieza cuando termina esta
            desde_sim = datetime.combine(f, h) + timedelta(minutes=dur)
        except Exception:
            c.eta_fecha = None
            c.eta_hora = None

    # Métricas M/M/1 (Wq viene en horas)
    mm1 = metrics_payload()
    Wq_min = None
    if mm1.get("Wq") is not None:
        Wq_min = mm1["Wq"] * 60.0
    mm1["Wq_min"] = Wq_min

    return render(
        request,
        "citaciones/pendientes.html",
        {"rows": qs, "mm1": mm1},
    )


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


# ==============================
#  Vista rango de agendadas
# ==============================

@login_required
@require_http_methods(["GET"])
def agendadas_rango(request):
    if not es_director(request.user):
        return HttpResponseForbidden()

    # Rangos por defecto: hoy ±3 días
    hoy = localdate()
    dias = int(request.GET.get("dias", 3) or 3)
    desde_str = request.GET.get("desde")
    desde = parse_date(desde_str) if desde_str else hoy - timedelta(days=dias)
    hasta = desde + timedelta(days=dias)

    qs = Citacion.objects.filter(
        estado__in=[Citacion.Estado.AGENDADA, Citacion.Estado.NOTIFICADA],
        fecha_citacion__gte=desde,
        fecha_citacion__lte=hasta,
    ).order_by("fecha_citacion", "hora_citacion")

    # Agrupar por día
    por_dia = {}
    for c in qs:
        por_dia.setdefault(c.fecha_citacion, []).append(c)

    # Navegación rápida
    prev_desde = desde - timedelta(days=dias)
    next_desde = desde + timedelta(days=dias)

    ctx = {
        "desde": desde,
        "hasta": hasta,
        "dias": dias,
        "por_dia": por_dia,
        "total": qs.count(),
        "hoy": hoy,
        "prev_desde": prev_desde,
        "next_desde": next_desde,
    }
    return render(request, "citaciones/agendadas_rango.html", ctx)


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

    return render(request, "citaciones/editar.html", {"form": form, "citacion": c})
