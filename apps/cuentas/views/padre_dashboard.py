# apps/cuentas/views/padre_dashboard.py

from django.shortcuts import render

from apps.cuentas.decorators import role_required
from apps.estudiantes.models.estudiante import Estudiante
from apps.estudiantes.models.asistencia import Asistencia
from apps.citaciones.models.citacion import Citacion


@role_required("Padre")
def padre_dashboard(request):
    # Hijos vinculados a este padre
    hijos = Estudiante.objects.filter(padre=request.user).select_related("curso")
    hijos_ids = [h.id for h in hijos]

    # resumen simple
    total_hijos = len(hijos_ids)

    total_citaciones = Citacion.objects.filter(estudiante_id__in=hijos_ids).count()
    total_faltas = Asistencia.objects.filter(
        estudiante_id__in=hijos_ids,
        estado=Asistencia.Estado.FALTA
    ).count()
    total_atrasos = Asistencia.objects.filter(
        estudiante_id__in=hijos_ids,
        estado=Asistencia.Estado.ATRASO
    ).count()

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

    context = {
        "hijos": hijos,
        "total_hijos": total_hijos,
        "total_citaciones": total_citaciones,
        "total_faltas": total_faltas,
        "total_atrasos": total_atrasos,
        "ultimas_citaciones": ultimas_citaciones,
        "ultimas_asistencias": ultimas_asistencias,
    }
    return render(request, "cuentas/padre_dashboard.html", context)
