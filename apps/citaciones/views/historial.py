# apps/citaciones/views/historial.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from apps.estudiantes.models.estudiante import Estudiante
from apps.citaciones.models.citacion import Citacion


@login_required
def historial_estudiante(request, estudiante_id: int):
    """
    Muestra todas las citaciones asociadas a un estudiante.
    """
    estudiante = get_object_or_404(Estudiante, pk=estudiante_id)

    citaciones = (
        Citacion.objects
        .filter(estudiante=estudiante)
        .select_related("aprobado_por")
        .order_by("-creado_en")
    )

    ctx = {
        "estudiante": estudiante,
        "citaciones": citaciones,
    }
    return render(request, "citaciones/historial_estudiante.html", ctx)
