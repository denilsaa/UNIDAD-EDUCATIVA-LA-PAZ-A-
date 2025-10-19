# apps/cuentas/views/director_dashboard.py
from django.shortcuts import render
from apps.cuentas.models import Usuario, Rol
from apps.cursos.models import Curso
from apps.estudiantes.models.estudiante import Estudiante
from apps.estudiantes.models.kardex_registro import KardexRegistro

def director_dashboard(request):
    usuarios = Usuario.objects.all()

    # Conteo por rol
    director_count   = Usuario.objects.filter(rol__nombre__iexact="DIRECTOR").count()
    regente_count    = Usuario.objects.filter(rol__nombre__iexact="REGENTE").count()
    secretaria_count = Usuario.objects.filter(rol__nombre__iexact="SECRETARIA").count()
    padre_count      = Usuario.objects.filter(rol__nombre__iexact="PADRE").count()

    # Cursos
    curso_count = Curso.objects.count()
    # Ajusta el campo si tu modelo usa otro timestamp (p. ej. created_at)
    try:
        ultimos_cursos = Curso.objects.order_by("-creado_en")[:5]
    except Exception:
        ultimos_cursos = Curso.objects.order_by("-id")[:5]

    # ===== NUEVO: Estudiantes =====
    estudiante_count = Estudiante.objects.count()
    # Trae curso y padre para mostrar en la tabla sin consultas extra
    ultimos_estudiantes = (
        Estudiante.objects
        .select_related("curso", "padre")
        .order_by("-id")[:10]
    )

    # ===== NUEVO (opcional): Últimos registros de Kárdex) =====
    # Si quieres también mostrarlos en el dashboard, añade el bloque en la plantilla.
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

        # nuevos:
        "estudiante_count": estudiante_count,
        "ultimos_estudiantes": ultimos_estudiantes,
        "ultimos_kardex": ultimos_kardex,  # usar solo si lo muestras en la plantilla
    }
    return render(request, "dashboard/director_dashboard.html", context)
