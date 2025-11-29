# IMPORTS que vas a necesitar al inicio del archivo de vistas
from datetime import date, timedelta

from django.db.models import Count, Sum, Case, When, IntegerField
from django.shortcuts import render
from django.utils.timezone import localdate

from apps.cuentas.decorators import role_required
from apps.cursos.models import Curso
from apps.estudiantes.models.estudiante import Estudiante
from apps.estudiantes.models.asistencia import Asistencia
from apps.citaciones.models.citacion import Citacion


@role_required("Regente")
def regente_dashboard(request):
    hoy = localdate() or date.today()

    # === Cursos y estudiantes a cargo del regente ===
    cursos = Curso.objects.filter(regente=request.user)
    est_qs = Estudiante.objects.filter(curso__in=cursos)

    total_cursos = cursos.count()
    total_estudiantes = est_qs.count()

    # === Asistencia HOY (para KPI y donut) ===
    asis_hoy_qs = Asistencia.objects.filter(estudiante__in=est_qs, fecha=hoy)
    counts_hoy = asis_hoy_qs.values("estado").annotate(c=Count("id"))
    mapa_hoy = {row["estado"]: row["c"] for row in counts_hoy}

    presentes_hoy = mapa_hoy.get(Asistencia.Estado.PRESENTE, 0)
    faltas_hoy = mapa_hoy.get(Asistencia.Estado.FALTA, 0)
    atrasos_hoy = mapa_hoy.get(Asistencia.Estado.ATRASO, 0)
    total_marcas_hoy = presentes_hoy + faltas_hoy + atrasos_hoy

    reg_asistencia_hoy = {
        "presentes": presentes_hoy,
        "faltas": faltas_hoy,
        "atrasos": atrasos_hoy,
    }
    pct_presentes_hoy = (
        int(round(presentes_hoy * 100.0 / total_marcas_hoy))
        if total_marcas_hoy
        else None
    )

    # === Asistencia por mes (últimos 6 meses) ===
    labels_meses = []
    values_meses = []

    base = hoy.replace(day=1)
    for i in range(5, -1, -1):
        # calculamos año/mes i meses atrás
        y = base.year
        m = base.month - i
        while m <= 0:
            y -= 1
            m += 12

        label = f"{m:02d}/{y}"
        labels_meses.append(label)

        mes_qs = Asistencia.objects.filter(
            estudiante__in=est_qs,
            fecha__year=y,
            fecha__month=m,
        )
        total_mes = mes_qs.count()
        pres_mes = mes_qs.filter(estado=Asistencia.Estado.PRESENTE).count()
        pct_mes = int(round(pres_mes * 100.0 / total_mes)) if total_mes else 0
        values_meses.append(pct_mes)

    reg_asistencia_meses = {
        "labels": labels_meses,
        "values": values_meses,
    }

    # === Faltas y atrasos por curso (últimos 30 días) ===
    desde_30 = hoy - timedelta(days=30)
    faltas_curso_qs = (
        Asistencia.objects.filter(estudiante__in=est_qs, fecha__gte=desde_30)
        .values("estudiante__curso__id", "estudiante__curso__nombre")
        .annotate(
            faltas=Sum(
                Case(
                    When(estado=Asistencia.Estado.FALTA, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
            atrasos=Sum(
                Case(
                    When(estado=Asistencia.Estado.ATRASO, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
        )
        .order_by("estudiante__curso__nombre")
    )

    reg_faltas_curso = [
        {
            "curso": row["estudiante__curso__nombre"],
            "faltas": row["faltas"] or 0,
            "atrasos": row["atrasos"] or 0,
        }
        for row in faltas_curso_qs
    ]

    # === Citaciones por estado (todos sus cursos) ===
    cit_qs = Citacion.objects.filter(estudiante__curso__in=cursos)
    cit_estado_counts = cit_qs.values("estado").annotate(c=Count("id"))
    reg_citaciones_estado = {row["estado"]: row["c"] for row in cit_estado_counts}

    # === Citaciones próximas para tabla (próximos 15 días) ===
    hasta = hoy + timedelta(days=15)
    citaciones_proximas = (
        Citacion.objects.filter(
            estudiante__curso__in=cursos,
            estado__in=[
                Citacion.Estado.AGENDADA,
                Citacion.Estado.NOTIFICADA,
            ],
            fecha_citacion__gte=hoy,
            fecha_citacion__lte=hasta,
        )
        .select_related("estudiante", "estudiante__curso")
        .order_by("fecha_citacion", "hora_citacion")[:10]
    )

    ctx = {
        "hoy": hoy,
        "total_cursos": total_cursos,
        "total_estudiantes": total_estudiantes,
        "pct_presentes_hoy": pct_presentes_hoy,
        "total_marcas_hoy": total_marcas_hoy,
        "citaciones_proximas": citaciones_proximas,

        # datos para gráficos (JSON)
        "reg_asistencia_hoy": reg_asistencia_hoy,
        "reg_asistencia_meses": reg_asistencia_meses,
        "reg_faltas_curso": reg_faltas_curso,
        "reg_citaciones_estado": reg_citaciones_estado,
    }
    return render(request, "cuentas/regente_dashboard.html", ctx)
