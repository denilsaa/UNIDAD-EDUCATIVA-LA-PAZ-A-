# apps/cursos/views/cursos.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from apps.cursos.models import Curso
from apps.cursos.forms import CursoForm

@login_required
def lista_cursos(request):
    q = (request.GET.get("q") or "").strip()
    cursos = Curso.objects.all().order_by("nivel", "paralelo")
    if q:
        cursos = cursos.filter(nivel__icontains=q) | cursos.filter(paralelo__icontains=q)
    return render(request, "cursos/lista_cursos.html", {"cursos": cursos, "q": q})

@login_required
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
    curso = get_object_or_404(Curso, id=curso_id)
    return render(request, "cursos/ver_curso.html", {"curso": curso})

@login_required
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

@login_required
def eliminar_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    if request.method == "POST":
        curso.delete()
        messages.success(request, "Curso eliminado correctamente.")
        return redirect(reverse("cursos:lista_cursos"))
    return render(request, "cursos/eliminar_curso.html", {"curso": curso})
