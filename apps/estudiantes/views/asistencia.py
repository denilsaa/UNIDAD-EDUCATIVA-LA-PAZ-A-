from datetime import date
import calendar

from django.contrib import messages
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now
from django.views.decorators.http import require_http_methods

from apps.cuentas.decorators import role_required
from apps.cursos.models import Curso
from apps.estudiantes.forms.asistencia import (
    CalendarioAsistenciaForm,
    ExclusionAsistenciaForm,
    build_registro_formset,
)
from apps.estudiantes.models.asistencia import Asistencia
from apps.estudiantes.models.asistencia_config import (
    AsistenciaCalendario,
    AsistenciaExclusion,
)
from apps.estudiantes.models.estudiante import Estudiante


# =========================
# Helpers
# =========================
def _usuario_puede_marcar_curso(u, curso: Curso) -> bool:
    """Director: siempre; Regente: solo si es su curso."""
    rol = (getattr(u, "rol", None) and getattr(u.rol, "nombre", "") or "").lower()
    if rol == "director":
        return True
    if rol == "regente":
        return curso.regente_id == u.id
    return False


def _cal_activo():
    return AsistenciaCalendario.objects.filter(activo=True).order_by("-creado_en").first()


# =========================
# Director: calendario + resumen mensual
# =========================
@role_required("director")
@require_http_methods(["GET", "POST"])
def asistencia_calendario(request):
    """
    - Crea/activa un calendario (POST).
    - Lista calendarios existentes.
    - Muestra un resumen mensual (P/F/R) del calendario ACTIVO filtrando por anio/mes.
    """
    form = CalendarioAsistenciaForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            cal = form.save(commit=False)
            cal.creado_por = request.user
            cal.activo = True
            cal.full_clean()
            cal.save()
            messages.success(request, "Calendario de asistencia guardado y activado.")
            return redirect("estudiantes:asistencia_calendario")
        messages.error(request, "Revisa el formulario.")

    calendarios = AsistenciaCalendario.objects.all()

    # Filtros de mes/año para el resumen
    hoy = now().date()
    try:
        year = int(request.GET.get("anio") or hoy.year)
        month = int(request.GET.get("mes") or hoy.month)
    except ValueError:
        year, month = hoy.year, hoy.month

    cal_activo = _cal_activo()

    resumen = {
        "year": year,
        "month": month,
        "dias_habiles": 0,
        "cuenta_P": 0,
        "cuenta_F": 0,
        "cuenta_R": 0,
        "pct_P": 0,
        "pct_F": 0,
        "pct_R": 0,
        "tiene_calendario": bool(cal_activo),
    }

    if cal_activo:
        _, last_day = calendar.monthrange(year, month)
        days = [date(year, month, d) for d in range(1, last_day + 1)]
        dias_validos = [d for d in days if cal_activo.admite_fecha(d)]
        resumen["dias_habiles"] = len(dias_validos)

        if dias_validos:
            asist_data = (
                Asistencia.objects
                .filter(fecha__year=year, fecha__month=month, fecha__in=dias_validos)
                .values("estado")
                .annotate(c=Count("id"))
            )
            by_estado = {row["estado"]: row["c"] for row in asist_data}
            resumen["cuenta_P"] = by_estado.get(Asistencia.Estado.PRESENTE, 0)
            resumen["cuenta_F"] = by_estado.get(Asistencia.Estado.FALTA, 0)
            resumen["cuenta_R"] = by_estado.get(Asistencia.Estado.ATRASO, 0)

            total = resumen["cuenta_P"] + resumen["cuenta_F"] + resumen["cuenta_R"]
            if total:
                resumen["pct_P"] = int(round(resumen["cuenta_P"] * 100.0 / total))
                resumen["pct_F"] = int(round(resumen["cuenta_F"] * 100.0 / total))
                resumen["pct_R"] = int(round(resumen["cuenta_R"] * 100.0 / total))

        ctx = {
            "form": form,
            "calendarios": calendarios,
            "resumen": resumen,
            "meses": list(range(1, 13)),  # ← agregamos meses para el template
        }
        return render(request, "asistencia/calendario_lista.html", ctx)



# =========================
# Director: exclusiones del calendario
# =========================
@role_required("director")
@require_http_methods(["GET", "POST"])
def asistencia_exclusiones(request, cal_id):
    cal = get_object_or_404(AsistenciaCalendario, pk=cal_id)
    form = ExclusionAsistenciaForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            ex = form.save(commit=False)
            ex.calendario = cal
            ex.full_clean()
            ex.save()
            messages.success(request, "Día marcado como sin lista.")
            return redirect("estudiantes:asistencia_exclusiones", cal_id=cal.id)
        messages.error(request, "No se pudo agregar la exclusión.")
    exclusiones = cal.exclusiones.all()
    return render(
        request,
        "asistencia/exclusiones_manage.html",
        {"calendario": cal, "form": form, "exclusiones": exclusiones},
    )


@role_required("director")
@require_http_methods(["POST"])
def asistencia_exclusion_eliminar(request, cal_id, excl_id):
    cal = get_object_or_404(AsistenciaCalendario, pk=cal_id)
    ex = get_object_or_404(AsistenciaExclusion, pk=excl_id, calendario=cal)
    ex.delete()
    messages.success(request, "Exclusión eliminada.")
    return redirect("estudiantes:asistencia_exclusiones", cal_id=cal.id)


# =========================
# Director/Regente: tomar asistencia por curso/fecha
# =========================
@role_required("director", "regente")
@require_http_methods(["GET", "POST"])
def asistencia_tomar(request, curso_id):
    """
    Un template único con 3 modos:
      - modo=dia  (por defecto): marcar un día.
      - modo=mes:  matriz editable (días hábiles del mes).
      - modo=anio: selector de año → enlaces a meses.
    """
    curso = get_object_or_404(Curso, pk=curso_id)
    if not _usuario_puede_marcar_curso(request.user, curso):
        messages.error(request, "No tienes permiso para este curso.")
        return redirect("cuentas:director_dashboard")

    modo = (request.GET.get("modo") or request.POST.get("modo") or "dia").lower()
    hoy = now().date()
    cal = _cal_activo()
    if not cal:
        messages.error(request, "No hay calendario de asistencia activo.")
        return redirect("estudiantes:asistencia_calendario")

    ctx_base = {"curso": curso, "modo": modo}

    # ====== DIARIO ======
    if modo == "dia":
        try:
            f_str = request.GET.get("fecha") or request.POST.get("fecha")
            f_obj = date.fromisoformat(f_str) if f_str else hoy
        except ValueError:
            f_obj = hoy

        if not cal.admite_fecha(f_obj):
            messages.error(request, "La fecha no admite asistencia (fuera de rango, fin de semana o excluida).")
            return redirect("cuentas:director_dashboard")

        estudiantes = Estudiante.objects.filter(curso=curso).order_by("apellidos", "nombres")
        formset = build_registro_formset(estudiantes)

        if request.method == "POST":
            with transaction.atomic():
                for form in formset:
                    px = form.prefix
                    est_id = int(request.POST.get(f"{px}-estudiante_id"))
                    estado = request.POST.get(f"{px}-estado")
                    est = estudiantes.get(id=est_id)
                    Asistencia.objects.update_or_create(
                        estudiante=est, fecha=f_obj, defaults={"estado": estado}
                    )
            messages.success(request, f"Asistencia de {f_obj} guardada.")
            return redirect(f"{request.path}?modo=dia&fecha={f_obj.isoformat()}")

        return render(
            request,
            "asistencia/tomar_asistencia.html",
            {**ctx_base, "fecha": f_obj, "formset": formset},
        )

    # ====== MENSUAL ======
    if modo == "mes":
        try:
            year = int(request.GET.get("anio") or request.POST.get("anio") or hoy.year)
            month = int(request.GET.get("mes") or request.POST.get("mes") or hoy.month)
        except ValueError:
            year, month = hoy.year, hoy.month

        import calendar as _cal
        _, last_day = _cal.monthrange(year, month)
        days_all = [date(year, month, d) for d in range(1, last_day + 1)]
        dias_validos = [d for d in days_all if cal.admite_fecha(d)]

        estudiantes = list(
            Estudiante.objects.filter(curso=curso).order_by("apellidos", "nombres").only("id", "apellidos", "nombres")
        )

        ids = [e.id for e in estudiantes] if estudiantes else []
        asis_qs = (
            Asistencia.objects.filter(estudiante_id__in=ids, fecha__year=year, fecha__month=month)
            .values("estudiante_id", "fecha", "estado")
        )
        asis_map = {(a["estudiante_id"], a["fecha"]): a["estado"] for a in asis_qs}

        if request.method == "POST":
            with transaction.atomic():
                for e in estudiantes:
                    for d in dias_validos:
                        key_est = f"s{e.id}_d{d.day}_estado"
                        val = (request.POST.get(key_est) or "").strip()
                        if val in (Asistencia.Estado.PRESENTE, Asistencia.Estado.FALTA, Asistencia.Estado.ATRASO):
                            Asistencia.objects.update_or_create(
                                estudiante=e, fecha=d, defaults={"estado": val}
                            )
                        else:
                            if (e.id, d) in asis_map:
                                Asistencia.objects.filter(estudiante=e, fecha=d).delete()
            messages.success(request, f"Asistencia mensual {month}/{year} guardada.")
            return redirect(f"{request.path}?modo=mes&anio={year}&mes={month}")

        # Construcción de la matriz y totales
        dia_ini = ["L", "M", "X", "J", "V", "S", "D"]
        headers = [{"day": d.day, "ini": dia_ini[d.weekday()]} for d in dias_validos]

        filas = []
        for e in estudiantes:
            celdas = []
            cP = cF = cR = 0
            for d in dias_validos:
                estado = asis_map.get((e.id, d), "")
                if estado == Asistencia.Estado.PRESENTE: cP += 1
                elif estado == Asistencia.Estado.FALTA:  cF += 1
                elif estado == Asistencia.Estado.ATRASO: cR += 1
                celdas.append({
                    "dia": d.day,
                    "estado": estado,
                    "name_estado": f"s{e.id}_d{d.day}_estado",
                })
            H = len(dias_validos)
            filas.append({
                "est": e, "celdas": celdas,
                "totP": cP, "totF": cF, "totR": cR,
                "pctP": int(round((cP/H)*100)) if H else 0,
                "pctF": int(round((cF/H)*100)) if H else 0,
                "pctR": int(round((cR/H)*100)) if H else 0,
            })

        MESES_ES = ["","Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

        return render(
            request,
            "asistencia/tomar_asistencia.html",
            {
                **ctx_base,
                "year": year, "month": month, "mes_nombre": MESES_ES[month],
                "headers": headers, "filas": filas,
            },
        )

    # ====== ANUAL ======
    try:
        year = int(request.GET.get("anio") or hoy.year)
    except ValueError:
        year = hoy.year

    MESES_ES = [
        (1, "Enero"), (2, "Febrero"), (3, "Marzo"), (4, "Abril"),
        (5, "Mayo"), (6, "Junio"), (7, "Julio"), (8, "Agosto"),
        (9, "Septiembre"), (10, "Octubre"), (11, "Noviembre"), (12, "Diciembre"),
    ]
    return render(
        request,
        "asistencia/tomar_asistencia.html",
        {**ctx_base, "year": year, "meses": MESES_ES},
    )


# =========================
# Padre: ver asistencia de su hijo/a
# =========================
@role_required("padre")
def asistencia_padre_detalle(request, estudiante_id):
    est = get_object_or_404(Estudiante, pk=estudiante_id, padre=request.user)
    registros = est.asistencias.all().order_by("-fecha")[:200]
    return render(
        request, "asistencia/padre_detalle.html", {"estudiante": est, "registros": registros}
    )
