# apps/estudiantes/views/padre.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, View
from django.http import HttpResponseForbidden

from apps.estudiantes.models.estudiante import Estudiante
from apps.cuentas.roles import es_padre

@method_decorator(login_required, name="dispatch")
class MisHijosListView(ListView):
    """
    Lista de hijos del padre autenticado.
    """
    model = Estudiante
    template_name = "estudiantes/mis_hijos.html"
    context_object_name = "hijos"

    def get_queryset(self):
        if not es_padre(self.request.user):
            return Estudiante.objects.none()
        return (Estudiante.objects
                .select_related("curso")
                .filter(padre_id=self.request.user.id)
                .order_by("curso__nivel", "apellidos", "nombres"))


@method_decorator(login_required, name="dispatch")
class HijoDetalleView(View):
    """
    Ficha resumida del hijo (datos básicos + accesos rápidos).
    """
    template_name = "estudiantes/hijo_detalle.html"

    def get(self, request, estudiante_id):
        hijo = get_object_or_404(Estudiante.objects.select_related("curso", "padre"), pk=estudiante_id)

        # 🔒 solo si es su hijo
        if not es_padre(request.user) or hijo.padre_id != request.user.id:
            return HttpResponseForbidden("No autorizado.")

        # (Si en el futuro agregas asistencia, se puede sumar aquí.)
        contexto = {
            "hijo": hijo,
        }
        return render(request, self.template_name, contexto)
