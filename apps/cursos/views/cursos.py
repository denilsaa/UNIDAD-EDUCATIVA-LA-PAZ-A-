# apps/cursos/views/cursos.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.db.models import Q

from apps.cursos.models import Curso
from apps.cursos.forms import CursoForm

# 🔒 utilidades de rol
from apps.cuentas.decorators import role_required
from apps.cuentas.roles import es_director, es_regente


# ============================
#   SOLO DIRECTOR
# ============================

@role_required("director")
def lista_cursos(request):
    q = (request.GET.get("q") or "").strip()
    cursos = Curso.objects.all().order_by("nivel", "paralelo")
    if q:
        cursos = cursos.filter(Q(nivel__icontains=q) | Q(paralelo__icontains=q))
    return render(request, "cursos/lista_cursos.html", {"cursos": cursos, "q": q})


@role_required("director")
def crear_curso(request):
    if request.method == "POST":
        form = CursoForm(request.POST)
        if form.is_valid():
            curso = form.save()
            messages.success(request, "Curso creado correctamente.")
            return redirect(reverse("cursos:ver_curso", args=[curso.id]))
        messages.error(request, "Por favor corrija los errores.")
    else:
        form = CursoForm()
    return render(request, "cursos/crear_curso.html", {"form": form})


@login_required
def ver_curso(request, curso_id):
    """
    Director: puede ver cualquier curso.
    Regente: solo puede ver si es regente del curso.
    Otros roles: 403.
    """
    curso = get_object_or_404(Curso, id=curso_id)

    if es_director(request.user):
        pass  # permitido
    elif es_regente(request.user):
        if getattr(curso, "regente_id", None) != request.user.id:
            return HttpResponseForbidden("No autorizado.")
    else:
        return HttpResponseForbidden("No autorizado.")

    return render(request, "cursos/ver_curso.html", {"curso": curso})


@role_required("director")
def editar_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    if request.method == "POST":
        form = CursoForm(request.POST, instance=curso)
        if form.is_valid():
            form.save()
            messages.success(request, "Curso actualizado correctamente.")
            return redirect(reverse("cursos:ver_curso", args=[curso.id]))
        messages.error(request, "Por favor corrija los errores.")
    else:
        form = CursoForm(instance=curso)
    return render(request, "cursos/editar_curso.html", {"form": form, "curso": curso})


@role_required("director")
@require_POST
def eliminar_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    curso.delete()
    messages.success(request, "Curso eliminado correctamente.")
    return redirect(reverse("cursos:lista_cursos"))


# ============================
#   REGENTE: SOLO SUS CURSOS
# ============================

@role_required("regente")
def mis_cursos_regente(request):
    """
    Listado de cursos del regente autenticado.
    """
    cursos = (
        Curso.objects
        .filter(regente_id=request.user.id)
        .order_by("nivel", "paralelo")
    )
    return render(request, "cursos/mis_cursos.html", {"cursos": cursos})
