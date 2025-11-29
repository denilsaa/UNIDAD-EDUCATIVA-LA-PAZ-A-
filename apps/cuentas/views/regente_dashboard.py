# apps/cuentas/views/regente_dashboard.py

from datetime import date

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

    # Cursos a cargo del regente
    cursos = Curso.objects.filter(regente=request.user)
    total_cursos = cursos.count()

    # Estudiantes de esos cursos
    estudiantes = Estudiante.objects.filter(curso__in=cursos)
    total_estudiantes = estudiantes.count()

    # Asistencia de HOY
    asis_hoy_qs = Asistencia.objects.filter(estudiante__in=estudiantes, fecha=hoy)
    total_marcas = asis_hoy_qs.count()
    presentes = asis_hoy_qs.filter(estado=Asistencia.Estado.PRESENTE).count()
    pct_presentes = int(round(presentes * 100.0 / total_marcas)) if total_marcas else None

    # Próximas citaciones (solo de sus cursos)
    citaciones_proximas = (
        Citacion.objects.filter(
            estudiante__curso__in=cursos,
            estado__in=[Citacion.Estado.AGENDADA, Citacion.Estado.NOTIFICADA],
        )
        .select_related("estudiante", "estudiante__curso")
        .order_by("fecha_citacion", "hora_citacion")[:5]
    )

    context = {
        "hoy": hoy,
        "cursos": cursos,
        "total_cursos": total_cursos,
        "total_estudiantes": total_estudiantes,
        "pct_presentes_hoy": pct_presentes,
        "total_marcas_hoy": total_marcas,
        "citaciones_proximas": citaciones_proximas,
    }
    return render(request, "cuentas/regente_dashboard.html", context)
