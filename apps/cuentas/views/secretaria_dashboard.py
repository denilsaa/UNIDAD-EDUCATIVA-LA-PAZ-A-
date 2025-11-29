# apps/cuentas/views/secretaria_dashboard.py

from django.shortcuts import render

from apps.cuentas.decorators import role_required
from apps.cuentas.models import Usuario
from apps.cursos.models import Curso
from apps.estudiantes.models.estudiante import Estudiante
from apps.citaciones.models.citacion import Citacion


@role_required("Secretaria", "Secretaría")
def secretaria_dashboard(request):
    total_estudiantes = Estudiante.objects.count()
    total_cursos = Curso.objects.count()
    total_padres = Usuario.objects.filter(rol__nombre__iexact="Padre").count()

    cit_pendientes = Citacion.objects.filter(estado=Citacion.Estado.ABIERTA).count()
    cit_agendadas = Citacion.objects.filter(
        estado__in=[Citacion.Estado.AGENDADA, Citacion.Estado.NOTIFICADA]
    ).count()

    context = {
        "total_estudiantes": total_estudiantes,
        "total_cursos": total_cursos,
        "total_padres": total_padres,
        "cit_pendientes": cit_pendientes,
        "cit_agendadas": cit_agendadas,
    }
    return render(request, "cuentas/secretaria_dashboard.html", context)
