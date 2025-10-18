# apps/cuentas/views/director_dashboard.py
from django.shortcuts import render
from apps.cuentas.models import Usuario, Rol    
from apps.cursos.models import Curso

def director_dashboard(request):
    usuarios = Usuario.objects.all()

    # Filtrar por el nombre del rol en el modelo relacionado
    director_count   = Usuario.objects.filter(rol__nombre__iexact="DIRECTOR").count()
    regente_count    = Usuario.objects.filter(rol__nombre__iexact="REGENTE").count()
    secretaria_count = Usuario.objects.filter(rol__nombre__iexact="SECRETARIA").count()
    padre_count      = Usuario.objects.filter(rol__nombre__iexact="PADRE").count()

    # Cursos (opcionales)
    curso_count = Curso.objects.count()
    ultimos_cursos = Curso.objects.order_by("-creado_en")[:5]

    context = {
        "usuarios": usuarios,
        "director_count": director_count,
        "regente_count": regente_count,
        "secretaria_count": secretaria_count,
        "padre_count": padre_count,
        "curso_count": curso_count,
        "ultimos_cursos": ultimos_cursos,
    }
    return render(request, "dashboard/director_dashboard.html", context)
