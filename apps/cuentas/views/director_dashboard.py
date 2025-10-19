# apps/cuentas/views/director_dashboard.py
from django.shortcuts import render
from apps.cuentas.models import Usuario, Rol
from apps.cursos.models import Curso
from apps.estudiantes.models.estudiante import Estudiante
from apps.estudiantes.models.kardex_registro import KardexRegistro

# ⬇️ IMPORTA EL DECORADOR DE ROL
from apps.cuentas.decorators import role_required


@role_required("director")  # ⬅️ SOLO DIRECTOR ENTRA AQUÍ
def director_dashboard(request):
    usuarios = Usuario.objects.all()

    # Conteo por rol
    director_count   = Usuario.objects.filter(rol__nombre__iexact="DIRECTOR").count()
    regente_count    = Usuario.objects.filter(rol__nombre__iexact="REGENTE").count()
    secretaria_count = Usuario.objects.filter(rol__nombre__iexact="SECRETARIA").count()
    padre_count      = Usuario.objects.filter(rol__nombre__iexact="PADRE").count()

    # Cursos
    curso_count = Curso.objects.count()
    try:
        ultimos_cursos = Curso.objects.order_by("-creado_en")[:5]
    except Exception:
        ultimos_cursos = Curso.objects.order_by("-id")[:5]

    # Estudiantes
    estudiante_count = Estudiante.objects.count()
    ultimos_estudiantes = (
        Estudiante.objects
        .select_related("curso", "padre")
        .order_by("-id")[:10]
    )

    # Últimos Kárdex (opcional mostrar en plantilla)
    ultimos_kardex = (
        KardexRegistro.objects
        .select_related("estudiante", "kardex_item")
        .order_by("-fecha", "-hora", "-id")[:10]
    )

    context = {
        "usuarios": usuarios,
        "director_count": director_count,
        "regente_count": regente_count,
        "secretaria_count": secretaria_count,
        "padre_count": padre_count,
        "curso_count": curso_count,
        "ultimos_cursos": ultimos_cursos,
        "estudiante_count": estudiante_count,
        "ultimos_estudiantes": ultimos_estudiantes,
        "ultimos_kardex": ultimos_kardex,
    }
    return render(request, "dashboard/director_dashboard.html", context)
