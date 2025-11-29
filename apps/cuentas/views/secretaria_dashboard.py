from datetime import date

from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.shortcuts import render

from apps.cuentas.decorators import role_required
from apps.cuentas.models import Usuario
from apps.cursos.models import Curso
from apps.estudiantes.models.estudiante import Estudiante
from apps.citaciones.models.citacion import Citacion


@role_required("Secretaria", "Secretaría")
def secretaria_dashboard(request):
    hoy = date.today()

    total_estudiantes = Estudiante.objects.count()
    total_cursos = Curso.objects.count()
    total_padres = Usuario.objects.filter(rol__nombre__iexact="Padre").count()

    cit_pendientes = Citacion.objects.filter(estado=Citacion.Estado.ABIERTA).count()
    cit_agendadas = Citacion.objects.filter(
        estado__in=[Citacion.Estado.AGENDADA, Citacion.Estado.NOTIFICADA]
    ).count()

    # === Donut: citaciones por estado ===
    cit_estado_qs = Citacion.objects.values("estado").annotate(c=Count("id"))
    sec_citaciones_estado = {row["estado"]: row["c"] for row in cit_estado_qs}

    # === Estudiantes por curso (Top 10) ===
    est_por_curso_qs = (
        Estudiante.objects.values("curso__id", "curso__nombre")
        .annotate(total=Count("id"))
        .order_by("-total")[:10]
    )
    sec_estudiantes_curso = [
        {
            "curso": row["curso__nombre"],
            "total": row["total"],
        }
        for row in est_por_curso_qs
    ]

    # === Altas de estudiantes por mes (últimos 12 meses) ===
    est_altas_qs = (
        Estudiante.objects.filter(creado_en__gte=hoy.replace(year=hoy.year - 1))
        .annotate(mes=TruncMonth("creado_en"))
        .values("mes")
        .annotate(total=Count("id"))
        .order_by("mes")
    )
    sec_altas_estudiantes = {
        "labels": [row["mes"].strftime("%b %Y") for row in est_altas_qs],
        "values": [row["total"] for row in est_altas_qs],
    }

    # === Citaciones por mes (pendientes vs cerradas) ===
    cit_mes_qs = (
        Citacion.objects.filter(creado_en__gte=hoy.replace(year=hoy.year - 1))
        .annotate(mes=TruncMonth("creado_en"))
        .values("mes")
        .annotate(
            abiertas=Count("id", filter=Citacion.objects.filter(estado=Citacion.Estado.ABIERTA)),
        )
    )
    # La forma de arriba con filter en Count es más avanzada;
    # para evitar problemas hacemos dos queries y las mezclamos en Python:

    cit_mes_base = (
        Citacion.objects.filter(creado_en__gte=hoy.replace(year=hoy.year - 1))
        .annotate(mes=TruncMonth("creado_en"))
        .values("mes")
        .annotate(total=Count("id"))
        .order_by("mes")
    )
    cit_mes_cerradas = (
        Citacion.objects.filter(
            creado_en__gte=hoy.replace(year=hoy.year - 1),
            estado__in=[
                Citacion.Estado.CERRADA,
                Citacion.Estado.RECHAZADA,
                Citacion.Estado.NOTIFICADA,
                Citacion.Estado.AGENDADA,
            ],
        )
        .annotate(mes=TruncMonth("creado_en"))
        .values("mes")
        .annotate(cerradas=Count("id"))
        .order_by("mes")
    )
    mapa_cerradas = {row["mes"]: row["cerradas"] for row in cit_mes_cerradas}

    labels_cit_mes = []
    abiertas_list = []
    cerradas_list = []
    for row in cit_mes_base:
        mes = row["mes"]
        total = row["total"]
        cerradas = mapa_cerradas.get(mes, 0)
        abiertas = max(total - cerradas, 0)

        labels_cit_mes.append(mes.strftime("%b %Y"))
        abiertas_list.append(abiertas)
        cerradas_list.append(cerradas)

    sec_citaciones_mes = {
        "labels": labels_cit_mes,
        "abiertas": abiertas_list,
        "cerradas": cerradas_list,
    }

    ctx = {
        "total_estudiantes": total_estudiantes,
        "total_cursos": total_cursos,
        "total_padres": total_padres,
        "cit_pendientes": cit_pendientes,
        "cit_agendadas": cit_agendadas,

        # Datos para gráficos
        "sec_citaciones_estado": sec_citaciones_estado,
        "sec_estudiantes_curso": sec_estudiantes_curso,
        "sec_altas_estudiantes": sec_altas_estudiantes,
        "sec_citaciones_mes": sec_citaciones_mes,
    }
    return render(request, "cuentas/secretaria_dashboard.html", ctx)
