# apps/cursos/views/cursos.py
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.cuentas.decorators import role_required
from apps.cuentas.roles import es_director, es_regente
from apps.cursos.forms import CursoForm
from apps.cursos.models import Curso


def _es_secretaria(user):
    """
    Devuelve True si el usuario tiene rol Secretaría.
    """
    nombre = getattr(getattr(user, "rol", None), "nombre", "") or ""
    return nombre.lower() in ("secretaria", "secretaría")


# ============================
#   DIRECTOR / SECRETARÍA
# ============================


@role_required("director", "secretaria", "secretaría")
def lista_cursos(request):
    q = (request.GET.get("q") or "").strip()
    cursos = Curso.objects.all().order_by("nivel", "paralelo")
    if q:
        cursos = cursos.filter(Q(nivel__icontains=q) | Q(paralelo__icontains=q))
    return render(request, "cursos/lista_cursos.html", {"cursos": cursos, "q": q})


@role_required("director", "secretaria", "secretaría")
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

    # 🔹 Obtener todos los cursos existentes para la validación JS
    cursos_existentes = list(Curso.objects.values("nivel", "paralelo"))

    # 🔹 Pasar los datos al contexto
    context = {
        "form": form,
        "cursos_json": json.dumps(cursos_existentes),
    }

    return render(request, "cursos/crear_curso.html", context)


@login_required
def ver_curso(request, curso_id):
    """
    Director: puede ver cualquier curso.
    Secretaría: puede ver cualquier curso.
    Regente: solo puede ver si es regente del curso.
    Otros roles: 403.
    """
    curso = get_object_or_404(Curso, id=curso_id)

    if es_director(request.user) or _es_secretaria(request.user):
        # acceso total
        pass
    elif es_regente(request.user):
        if getattr(curso, "regente_id", None) != request.user.id:
            return render(request, "403.html", status=403)
    else:
        return render(request, "403.html", status=403)

    return render(request, "cursos/ver_curso.html", {"curso": curso})


@role_required("director", "secretaria", "secretaría")
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

    # 🔹 Obtener todos los cursos excepto el actual, para verificar duplicados desde JS
    cursos_existentes = list(
        Curso.objects.exclude(id=curso.id).values("nivel", "paralelo")
    )

    context = {
        "form": form,
        "curso": curso,
        "cursos_json": json.dumps(cursos_existentes),
    }

    return render(request, "cursos/editar_curso.html", context)


@role_required("director")
def eliminar_curso(request, curso_id):
    """
    Con SET_NULL:
    - Al borrar el curso, Estudiante.curso y Kardex.curso quedan en NULL automáticamente.
    """
    curso = get_object_or_404(Curso, id=curso_id)

    # Obtener estudiantes asociados usando related_name "estudiantes"
    estudiantes = curso.estudiantes.all()

    if request.method == "POST":
        curso.delete()
        messages.success(request, "Curso eliminado permanentemente.")
        return redirect(reverse("cursos:lista_cursos"))

    return render(
        request,
        "cursos/eliminar_curso.html",
        {
            "curso": curso,
            "estudiantes": estudiantes,
        },
    )


# ============================
#   REGENTE: SOLO SUS CURSOS
# ============================


@role_required("regente")
def mis_cursos_regente(request):
    cursos = (
        Curso.objects.filter(regente_id=request.user.id).order_by("nivel", "paralelo")
    )
    return render(request, "cursos/mis_cursos.html", {"cursos": cursos})
