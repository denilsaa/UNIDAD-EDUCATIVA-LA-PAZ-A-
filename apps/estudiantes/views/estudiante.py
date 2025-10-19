# apps/estudiantes/views/estudiante.py
from datetime import date
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from apps.estudiantes.forms import EstudianteForm
from apps.estudiantes.models.estudiante import Estudiante
from apps.cursos.models.kardex import Kardex
from django.shortcuts import get_object_or_404
from apps.cursos.models.curso import Curso

def trimestre_actual(hoy: date) -> int:
    """Devuelve el trimestre actual (ajusta si tu calendario es distinto)."""
    if hoy.month <= 4:
        return 1
    if hoy.month <= 8:
        return 2
    return 3


class EstudianteListView(ListView):
    model = Estudiante
    template_name = "estudiantes/lista_estudiantes.html"
    paginate_by = 20

    def get_queryset(self):
        q = self.request.GET.get("q", "")
        qs = (
            Estudiante.objects
            .select_related("curso", "padre", "kardex")
            .order_by("apellidos", "nombres")
        )
        if q:
            qs = qs.filter(
                Q(apellidos__icontains=q) |
                Q(nombres__icontains=q) |
                Q(ci__icontains=q) |
                Q(curso__nivel__icontains=q) |
                Q(curso__paralelo__icontains=q)
            )
        return qs


class EstudianteCreateView(CreateView):
    model = Estudiante
    form_class = EstudianteForm
    template_name = "estudiantes/formulario_estudiante.html"
    success_url = reverse_lazy("estudiantes:listar")

    def form_valid(self, form):
        obj: Estudiante = form.save(commit=False)

        # Debe existir curso para poder asignar kárdex
        if not obj.curso_id:
            form.add_error("curso", "Debe seleccionar un curso.")
            return self.form_invalid(form)

        hoy = date.today()
        kardex, _ = Kardex.objects.get_or_create(
            curso=obj.curso,
            anio=hoy.year,
            trimestre=trimestre_actual(hoy),
            defaults={"observacion": ""},
        )

        obj.kardex = kardex
        obj.save()
        form.save_m2m()

        # Necesario para get_success_url en Django 5
        self.object = obj
        return HttpResponseRedirect(self.get_success_url())


class EstudianteUpdateView(UpdateView):
    model = Estudiante
    form_class = EstudianteForm
    template_name = "estudiantes/formulario_estudiante.html"
    success_url = reverse_lazy("estudiantes:listar")

    def form_valid(self, form):
        obj: Estudiante = form.save(commit=False)

        # Si no tiene kárdex (p.ej., migración antigua), créalo ahora
        if not obj.kardex_id and obj.curso_id:
            hoy = date.today()
            kardex, _ = Kardex.objects.get_or_create(
                curso=obj.curso,
                anio=hoy.year,
                trimestre=trimestre_actual(hoy),
                defaults={"observacion": ""},
            )
            obj.kardex = kardex

        obj.save()
        form.save_m2m()

        # Necesario para get_success_url en Django 5
        self.object = obj
        return HttpResponseRedirect(self.get_success_url())


class EstudianteDeleteView(DeleteView):
    model = Estudiante
    template_name = "estudiantes/confirmar_eliminacion_estudiante.html"
    success_url = reverse_lazy("estudiantes:listar")
    
class EstudiantesPorCursoListView(ListView):
    model = Estudiante
    template_name = "estudiantes/estudiantes_por_curso.html"
    paginate_by = 30

    def get_queryset(self):
        self.curso = get_object_or_404(Curso, pk=self.kwargs["curso_id"])
        q = self.request.GET.get("q", "")
        qs = (Estudiante.objects
              .filter(curso=self.curso)
              .select_related("curso", "padre")
              .order_by("apellidos", "nombres"))
        if q:
            qs = qs.filter(
                Q(apellidos__icontains=q) |
                Q(nombres__icontains=q) |
                Q(ci__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["curso"] = self.curso
        ctx["total"] = self.get_queryset().count()
        return ctx