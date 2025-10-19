# apps/estudiantes/views/estudiante.py
from datetime import date

from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404

from apps.estudiantes.forms import EstudianteForm
# (Estos imports no se usan en este archivo; puedes borrarlos si quieres)
# from apps.estudiantes.forms import KardexItemForm
# from apps.estudiantes.models.kardex_item import KardexItem

from apps.estudiantes.models.estudiante import Estudiante
from apps.cursos.models.kardex import Kardex
from apps.cursos.models.curso import Curso

# 🔒 roles/mixins
from apps.cuentas.mixins import RoleRequiredMixin
from apps.cuentas.roles import es_regente, es_director, es_secretaria


def trimestre_actual(hoy: date) -> int:
    """Devuelve el trimestre actual (ajusta si tu calendario es distinto)."""
    if hoy.month <= 4:
        return 1
    if hoy.month <= 8:
        return 2
    return 3


# ============
# CRUD GLOBAL (Director / Secretaría)
# ============

class EstudianteListView(RoleRequiredMixin, ListView):
    model = Estudiante
    template_name = "estudiantes/lista_estudiantes.html"
    paginate_by = 20
    required_roles = ("director", "secretaria", "secretaría")

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


class EstudianteCreateView(RoleRequiredMixin, CreateView):
    model = Estudiante
    form_class = EstudianteForm
    template_name = "estudiantes/formulario_estudiante.html"
    success_url = reverse_lazy("estudiantes:listar")
    required_roles = ("director", "secretaria", "secretaría")

    def form_valid(self, form):
        obj: Estudiante = form.save(commit=False)

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

        self.object = obj  # necesario para Django 5
        return HttpResponseRedirect(self.get_success_url())


class EstudianteUpdateView(RoleRequiredMixin, UpdateView):
    model = Estudiante
    form_class = EstudianteForm
    template_name = "estudiantes/formulario_estudiante.html"
    success_url = reverse_lazy("estudiantes:listar")
    required_roles = ("director", "secretaria", "secretaría")

    def form_valid(self, form):
        obj: Estudiante = form.save(commit=False)

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

        self.object = obj  # necesario para Django 5
        return HttpResponseRedirect(self.get_success_url())


class EstudianteDeleteView(RoleRequiredMixin, DeleteView):
    model = Estudiante
    template_name = "estudiantes/confirmar_eliminacion_estudiante.html"
    success_url = reverse_lazy("estudiantes:listar")
    required_roles = ("director",)  # si prefieres, agrega secretaría aquí


# ===========================
# LISTADO POR CURSO (Dir/Reg/Sec)
# ===========================

class EstudiantesPorCursoListView(RoleRequiredMixin, ListView):
    """
    Director / Secretaría: pueden ver cualquier curso.
    Regente: solo si es regente del curso.
    Padres: no ingresan aquí.
    """
    model = Estudiante
    template_name = "estudiantes/estudiantes_por_curso.html"
    paginate_by = 30
    required_roles = ("director", "regente", "secretaria", "secretaría")

    def dispatch(self, request, *args, **kwargs):
        # Cargamos el curso aquí para validar acceso del regente
        self.curso = get_object_or_404(Curso, pk=self.kwargs["curso_id"])

        # Si es regente, debe ser regente del curso
        if es_regente(request.user):
            if getattr(self.curso, "regente_id", None) != request.user.id:
                return HttpResponseForbidden("No autorizado.")

        # Director / Secretaría pasan sin restricción adicional
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        q = self.request.GET.get("q", "")
        qs = (
            Estudiante.objects
            .filter(curso=self.curso)
            .select_related("curso", "padre")
            .order_by("apellidos", "nombres")
        )
        if q:
            qs = qs.filter(
                Q(apellidos__icontains=q) |
                Q(nombres__icontains=q) |
                Q(ci__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Usa el queryset ya evaluado para contar sin repetir consultas
        qs = self.get_queryset()
        ctx["curso"] = self.curso
        ctx["total"] = qs.count()
        ctx["q"] = self.request.GET.get("q", "")
        return ctx
