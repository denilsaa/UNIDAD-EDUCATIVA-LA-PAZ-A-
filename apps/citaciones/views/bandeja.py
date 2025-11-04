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

from apps.citaciones.services.agenda_service import suggest_free_slot
from apps.citaciones.services.metrics_service import metrics_payload

from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required

from apps.citaciones.models.citacion import Citacion
from apps.citaciones.services.agenda_service import suggest_free_slot
from apps.citaciones.services.metrics_service import metrics_payload
from apps.citaciones.services import queue_service
from apps.cuentas.roles import es_director

from datetime import timedelta
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

    qs = Citacion.objects.filter(estado=Citacion.Estado.ABIERTA).order_by("-creado_en")

    # ➜ anotar ETA en cada objeto (evitamos usar dict por id en el template)
    for c in qs:
        try:
            f, h = suggest_free_slot(duracion_min=c.duracion_min or None)
            c.eta_fecha = f
            c.eta_hora = h
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

@login_required
@require_http_methods(["GET"])
def agendadas_rango(request):
    """
    Agenda por rango: muestra AGENDADAS agrupadas por día.
    Params opcionales:
      - desde=YYYY-MM-DD (default: hoy)
      - dias=int (default: 7)  -> muestra [desde ... desde+dias-1]
    """
    if not es_director(request.user):
        return HttpResponseForbidden()

    hoy = localdate()
    desde = parse_date(request.GET.get("desde") or "") or hoy
    dias = request.GET.get("dias")
    try:
        dias = int(dias) if dias is not None else 7
    except Exception:
        dias = 7
    if dias < 1:
        dias = 1
    if dias > 31:
        dias = 31  # límite sano

    hasta = desde + timedelta(days=dias - 1)

    qs = (
        Citacion.objects
        .filter(
            estado=Citacion.Estado.AGENDADA,
            fecha_citacion__gte=desde,
            fecha_citacion__lte=hasta,
        )
        .order_by("fecha_citacion", "hora_citacion", "id")
    )

    # Agrupar por fecha en un dict {fecha: [citaciones...]}
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