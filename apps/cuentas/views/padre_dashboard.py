from datetime import date, timedelta

from django.db.models import Count, Sum, Case, When, IntegerField
from django.shortcuts import render
from django.utils.timezone import localdate

from apps.cuentas.decorators import role_required
from apps.estudiantes.models.estudiante import Estudiante
from apps.estudiantes.models.asistencia import Asistencia
from apps.citaciones.models.citacion import Citacion


@role_required("Padre")
def padre_dashboard(request):
    hoy = localdate() or date.today()

    hijos = Estudiante.objects.filter(padre=request.user).select_related("curso")
    hijos_ids = list(hijos.values_list("id", flat=True))
    total_hijos = len(hijos_ids)

    # Citaciones / faltas / atrasos globales
    total_citaciones = Citacion.objects.filter(estudiante_id__in=hijos_ids).count()
    total_faltas = Asistencia.objects.filter(
        estudiante_id__in=hijos_ids,
        estado=Asistencia.Estado.FALTA,
    ).count()
    total_atrasos = Asistencia.objects.filter(
        estudiante_id__in=hijos_ids,
        estado=Asistencia.Estado.ATRASO,
    ).count()

    # === Asistencia del mes actual (donut) ===
    year = hoy.year
    month = hoy.month
    asis_mes_qs = Asistencia.objects.filter(
        estudiante_id__in=hijos_ids, fecha__year=year, fecha__month=month
    )
    asis_mes_counts = asis_mes_qs.values("estado").annotate(c=Count("id"))
    mapa_mes = {row["estado"]: row["c"] for row in asis_mes_counts}

    pad_asistencia_mes = {
        "presentes": mapa_mes.get(Asistencia.Estado.PRESENTE, 0),
        "faltas": mapa_mes.get(Asistencia.Estado.FALTA, 0),
        "atrasos": mapa_mes.get(Asistencia.Estado.ATRASO, 0),
    }

    # === Evolución de asistencia (últimos 6 meses) ===
    labels_meses = []
    values_meses = []
    base = hoy.replace(day=1)
    for i in range(5, -1, -1):
        y = base.year
        m = base.month - i
        while m <= 0:
            y -= 1
            m += 12

        label = f"{m:02d}/{y}"
        labels_meses.append(label)

        mes_qs = Asistencia.objects.filter(
            estudiante_id__in=hijos_ids,
            fecha__year=y,
            fecha__month=m,
        )
        total_mes = mes_qs.count()
        pres_mes = mes_qs.filter(estado=Asistencia.Estado.PRESENTE).count()
        pct_mes = int(round(pres_mes * 100.0 / total_mes)) if total_mes else 0
        values_meses.append(pct_mes)

    pad_asistencia_meses = {
        "labels": labels_meses,
        "values": values_meses,
    }

    # === Faltas y atrasos por hijo (últimos 90 días) ===
    desde_90 = hoy - timedelta(days=90)
    faltas_hijo_qs = (
        Asistencia.objects.filter(
            estudiante_id__in=hijos_ids,
            fecha__gte=desde_90,
        )
        .values("estudiante_id", "estudiante__apellidos", "estudiante__nombres")
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
        .order_by("estudiante__apellidos", "estudiante__nombres")
    )

    pad_faltas_hijo = [
        {
            "estudiante": f'{row["estudiante__apellidos"]} {row["estudiante__nombres"]}',
            "faltas": row["faltas"] or 0,
            "atrasos": row["atrasos"] or 0,
        }
        for row in faltas_hijo_qs
    ]

    # === Últimas citaciones y asistencias para tablas ===
    ultimas_citaciones = (
        Citacion.objects.filter(estudiante_id__in=hijos_ids)
        .select_related("estudiante")
        .order_by("-fecha_citacion", "-creado_en")[:5]
    )

    ultimas_asistencias = (
        Asistencia.objects.filter(estudiante_id__in=hijos_ids)
        .select_related("estudiante")
        .order_by("-fecha")[:5]
    )

    ctx = {
        "hijos": hijos,
        "total_hijos": total_hijos,
        "total_citaciones": total_citaciones,
        "total_faltas": total_faltas,
        "total_atrasos": total_atrasos,
        "ultimas_citaciones": ultimas_citaciones,
        "ultimas_asistencias": ultimas_asistencias,

        # datos para gráficos
        "pad_asistencia_mes": pad_asistencia_mes,
        "pad_asistencia_meses": pad_asistencia_meses,
        "pad_faltas_hijo": pad_faltas_hijo,
    }
    return render(request, "cuentas/padre_dashboard.html", ctx)
