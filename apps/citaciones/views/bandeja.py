# apps/citaciones/views/bandeja.py

from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.dateparse import parse_date, parse_time
from django.utils.timezone import localdate
from django.views.decorators.http import require_http_methods, require_POST

from apps.citaciones.forms import CitacionEditForm
from apps.citaciones.models.citacion import Citacion
from apps.citaciones.models.config import AtencionConfig
from apps.citaciones.services import queue_service
from apps.citaciones.services.agenda_service import suggest_free_slot
from apps.citaciones.services.metrics_service import metrics_payload
from apps.citaciones.services.notify_service import resolve_padres_ids
from apps.citaciones.services.notificaciones_service import notificar_citacion_aprobada
from apps.cuentas.roles import es_director


# ==============================
#  Helpers de rol
# ==============================

def _es_secretaria(user):
    """
    Devuelve True si el usuario tiene rol Secretaría.
    """
    nombre = getattr(getattr(user, "rol", None), "nombre", "") or ""
    return nombre.lower() in ("secretaria", "secretaría")


def _es_regente(user):
    """
    Devuelve True si el usuario tiene rol Regente.
    """
    nombre = getattr(getattr(user, "rol", None), "nombre", "") or ""
    return "regente" in nombre.lower()


def _puede_manejar_citaciones(user):
    """
    Director y Secretaría pueden ver y gestionar citaciones
    (aprobar, editar, cancelar, notificar).
    """
    return es_director(user) or _es_secretaria(user)


# ==============================
#  Bandeja pendientes (aprobación)
# ==============================

@login_required
@require_http_methods(["GET"])
def pendientes(request):
    if not _puede_manejar_citaciones(request.user):
        return HttpResponseForbidden()

    # Ordenar por peso: mayor duración primero, luego por fecha de creación
    qs = (
        Citacion.objects.filter(estado=Citacion.Estado.ABIERTA)
        .order_by("-duracion_min", "-creado_en")
    )

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


# ==============================
#  Acciones sobre pendientes
# ==============================

@login_required
@require_POST
def aprobar(request, pk: int):
    if not _puede_manejar_citaciones(request.user):
        return HttpResponseForbidden()

    c = queue_service.aprobar(pk, request.user)
    return JsonResponse(
        {
            "ok": True,
            "id": c.id,
            "estado": c.estado,
            "fecha": c.fecha_citacion.isoformat() if c.fecha_citacion else None,
            "hora": c.hora_citacion.strftime("%H:%M") if c.hora_citacion else None,
        }
    )


@login_required
@require_POST
def editar(request, pk: int):
    """
    Edición vía AJAX (usada inicialmente por la cola).
    Mantengo esta vista porque la referencia existe en urls.py.
    """
    if not _puede_manejar_citaciones(request.user):
        return HttpResponseForbidden()

    fecha_str = request.POST.get("fecha")
    hora_str = request.POST.get("hora")
    dur_str = request.POST.get("duracion_min")

    fecha = parse_date(fecha_str) if fecha_str else None
    hora = parse_time(hora_str) if hora_str else None
    dur = int(dur_str) if dur_str else None

    c = queue_service.editar(pk, fecha, hora, dur, request.user)

    return JsonResponse({"ok": True, "id": c.id, "estado": c.estado})


@login_required
@require_POST
def rechazar(request, pk: int):
    if not _puede_manejar_citaciones(request.user):
        return HttpResponseForbidden()

    c = queue_service.rechazar(pk, request.user)
    return JsonResponse({"ok": True, "id": c.id, "estado": c.estado})


@login_required
@require_POST
def notificar(request, pk: int):
    if not _puede_manejar_citaciones(request.user):
        return HttpResponseForbidden()

    c = get_object_or_404(Citacion, id=pk)

    if c.estado != Citacion.Estado.NOTIFICADA:
        c.estado = Citacion.Estado.NOTIFICADA
        c.save(update_fields=["estado", "actualizado_en"])

    enviados = 0
    for padre_id in resolve_padres_ids(c.estudiante):
        notificar_citacion_aprobada(c, receptor_id=padre_id)
        enviados += 1

    if enviados == 0:
        return JsonResponse(
            {
                "ok": False,
                "error": "No se encontró ningún padre vinculado al estudiante.",
            }
        )

    return JsonResponse(
        {"ok": True, "id": c.id, "estado": c.estado, "enviados": enviados}
    )


# ==============================
#  Vista rango de agendadas (Director / Secretaría)
# ==============================

@login_required
@require_http_methods(["GET"])
def agendadas_rango(request):
    if not _puede_manejar_citaciones(request.user):
        return HttpResponseForbidden()

    hoy = localdate()

    # Si hoy es sábado (5) o domingo (6), mover al lunes siguiente
    if hoy.weekday() >= 5:
        offset = (7 - hoy.weekday()) % 7  # 2 para sábado, 1 para domingo
        if offset == 0:
            offset = 1
        desde_base = hoy + timedelta(days=offset)
    else:
        # Lunes–viernes: usar el día actual
        desde_base = hoy

    dias = int(request.GET.get("dias", 3) or 3)

    # Si el usuario manda "desde" por GET, respetarlo.
    desde_str = request.GET.get("desde")
    desde = parse_date(desde_str) if desde_str else desde_base
    if desde is None:
        desde = desde_base

    hasta = desde + timedelta(days=dias)

    qs = (
        Citacion.objects.filter(
            estado__in=[Citacion.Estado.AGENDADA, Citacion.Estado.NOTIFICADA],
            fecha_citacion__gte=desde,
            fecha_citacion__lte=hasta,
        )
        .select_related("estudiante", "estudiante__curso")
        .order_by("fecha_citacion", "hora_citacion")
    )

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
        "puede_gestionar_citaciones": True,
        "url_base": "citaciones:agendadas_rango",
    }
    return render(request, "citaciones/agendadas_rango.html", ctx)


# ==============================
#  Vista rango de agendadas (Regente: solo sus cursos)
# ==============================

@login_required
@require_http_methods(["GET"])
def agendadas_mis_cursos(request):
    """
    Regente: ve citaciones AGENDADAS / NOTIFICADAS SOLO de los cursos donde él es regente.
    No puede editarlas ni cancelarlas, solo consultar.
    """
    if not _es_regente(request.user):
        return HttpResponseForbidden()

    hoy = localdate()

    if hoy.weekday() >= 5:
        offset = (7 - hoy.weekday()) % 7
        if offset == 0:
            offset = 1
        desde_base = hoy + timedelta(days=offset)
    else:
        desde_base = hoy

    dias = int(request.GET.get("dias", 3) or 3)

    desde_str = request.GET.get("desde")
    desde = parse_date(desde_str) if desde_str else desde_base
    if desde is None:
        desde = desde_base

    hasta = desde + timedelta(days=dias)

    qs = (
        Citacion.objects.filter(
            estado__in=[Citacion.Estado.AGENDADA, Citacion.Estado.NOTIFICADA],
            fecha_citacion__gte=desde,
            fecha_citacion__lte=hasta,
            estudiante__curso__regente=request.user,
        )
        .select_related("estudiante", "estudiante__curso")
        .order_by("fecha_citacion", "hora_citacion")
    )

    por_dia = {}
    for c in qs:
        por_dia.setdefault(c.fecha_citacion, []).append(c)

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
        "puede_gestionar_citaciones": False,   # regente solo consulta
        "url_base": "citaciones:agendadas_mis_cursos",
    }
    return render(request, "citaciones/agendadas_rango.html", ctx)


# ==============================
#  Editar vía formulario clásico
# ==============================

@login_required
@require_http_methods(["GET", "POST"])
def editar_form(request, pk: int):
    if not _puede_manejar_citaciones(request.user):
        return HttpResponseForbidden()

    c = get_object_or_404(Citacion, id=pk)

    if request.method == "POST":
        form = CitacionEditForm(request.POST, instance=c)
        if form.is_valid():
            form.save()  # guarda fecha_citacion, hora_citacion y duracion_min
            return redirect("citaciones:pendientes")
    else:
        form = CitacionEditForm(instance=c)

    # Sugerencia informativa M/M/1
    sugerido = None
    try:
        cfg = AtencionConfig.objects.first()
        dur_def = int(getattr(cfg, "duracion_por_defecto", 30) or 30)
        dur = int(c.duracion_min or dur_def)
        f, h = suggest_free_slot(duracion_min=dur, desde=None)
        sugerido = datetime.combine(f, h)
    except Exception:
        sugerido = None

    return render(
        request,
        "citaciones/editar.html",
        {
            "form": form,
            "citacion": c,
            "sugerido": sugerido,
        },
    )


@login_required
@require_http_methods(["GET"])
def detalle_kardex(request, pk: int):
    """
    Devuelve en JSON los registros de Kárdex vinculados a esta citación
    para mostrarlos en un modal.

    LÓGICA ACUMULABLE:
    - Tomamos el kardex_registro asociado a la citación.
    - Buscamos TODOS los registros de Kárdex del MISMO estudiante y MISMA FECHA.
    - Así, si luego se añaden más registros ese día, también aparecerán aquí.
    """
    if not _puede_manejar_citaciones(request.user):
        return HttpResponseForbidden()

    c = get_object_or_404(
        Citacion.objects.select_related(
            "estudiante",
            "kardex_registro__kardex_item",
            "kardex_registro__docente",
        ),
        id=pk,
    )

    kr_base = c.kardex_registro
    if not kr_base:
        return JsonResponse(
            {
                "ok": False,
                "error": "Esta citación no tiene registros de Kárdex vinculados.",
            }
        )

    # Modelo real de los registros de Kárdex (lo inferimos del propio objeto)
    KardexRegistro = type(kr_base)

    # 🔁 Buscamos TODOS los registros del mismo estudiante y misma FECHA
    registros_qs = (
        KardexRegistro.objects.filter(
            estudiante=c.estudiante,
            fecha=kr_base.fecha,
        )
        .select_related("kardex_item", "docente")
        .order_by("hora", "id")
    )

    registros = []
    for kr in registros_qs:
        registros.append(
            {
                "id": kr.id,
                "fecha": kr.fecha.strftime("%Y-%m-%d"),
                "hora": kr.hora.strftime("%H:%M") if kr.hora else "",
                "item": kr.kardex_item.descripcion,
                "area": kr.kardex_item.get_area_display(),
                "sentido": kr.kardex_item.get_sentido_display(),
                "observacion": kr.observacion or "",
                "sello_maestro": kr.sello_maestro,
                "docente": str(kr.docente) if kr.docente else "",
            }
        )

    return JsonResponse(
        {
            "ok": True,
            "citacion": c.id,
            "estudiante": str(c.estudiante),
            "registros": registros,
        }
    )
