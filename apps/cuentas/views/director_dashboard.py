# apps/cuentas/views/director_dashboard.py
from django.shortcuts import render
from apps.cuentas.models import Usuario, Rol
from apps.cursos.models import Curso
from apps.estudiantes.models.estudiante import Estudiante
from apps.estudiantes.models.kardex_registro import KardexRegistro

# ⬇️ IMPORTA EL DECORADOR DE ROL
from apps.cuentas.decorators import role_required
from django.utils import timezone
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from datetime import timedelta

from apps.estudiantes.models.asistencia import Asistencia
from apps.estudiantes.models.kardex_item import KardexItem


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

    # ===== KPIs / GRÁFICAS =====
    hoy = timezone.localdate()

    # Asistencia hoy
    total_hoy = Asistencia.objects.filter(fecha=hoy).count()
    presentes = Asistencia.objects.filter(fecha=hoy, estado=Asistencia.Estado.PRESENTE).count()
    asistencia_hoy = round(presentes * 100 / total_hoy) if total_hoy else 0

    # Riesgo (operativo): % faltas+atrasos en últimos 30 días >= 20%
    desde = hoy - timedelta(days=30)
    faltas_qs = (Asistencia.objects
                .filter(fecha__gte=desde)
                .values("estudiante")
                .annotate(
                    total=Count("id"),
                    no_ok=Count("id", filter=Q(estado__in=[Asistencia.Estado.FALTA, Asistencia.Estado.ATRASO]))
                ))
    estudiantes_en_riesgo = sum(1 for r in faltas_qs if r["total"] and (r["no_ok"] / r["total"]) >= 0.20)
    total_est = Estudiante.objects.count() or 1
    pct_riesgo = round(estudiantes_en_riesgo * 100 / total_est)

    # Asistencia por mes (últimos 8)
    asis_mes = (Asistencia.objects
                .annotate(m=TruncMonth("fecha"))
                .values("m")
                .annotate(
                    total=Count("id"),
                    ok=Count("id", filter=Q(estado=Asistencia.Estado.PRESENTE))
                )
                .order_by("m")[:8])
    asistencia_por_mes = [{"mes": x["m"].strftime("%b"), "pct": round(x["ok"]*100/(x["total"] or 1))} for x in asis_mes]

    # Kárdex NEGATIVO por área
    negativos_por_area = list(
        KardexRegistro.objects.filter(kardex_item__sentido=KardexItem.Sentido.NEGATIVO)
        .values("kardex_item__area").annotate(total=Count("id")).order_by("-total")
    )
    negativos_por_area = [{"area": r["kardex_item__area"], "total": r["total"]} for r in negativos_por_area]

    # Negativos por día (7 días)
    negativos_semana = []
    for i in range(6,-1,-1):
        d = hoy - timedelta(days=i)
        t = KardexRegistro.objects.filter(
            fecha=d, kardex_item__sentido=KardexItem.Sentido.NEGATIVO
        ).count()
        negativos_semana.append({"dia": d.strftime("%a"), "total": t})

    # Usuarios por rol actuales (tus nombres reales)
    roles_counts = {
        "Directivo":          Usuario.objects.filter(rol__nombre__iexact="Directivo").count(),
        "Secretaría":         Usuario.objects.filter(rol__nombre__iexact="Secretaria").count(),
        "Regentes":           Usuario.objects.filter(rol__nombre__iexact="Regentes").count(),
        "Padres de Familia":  Usuario.objects.filter(rol__nombre__iexact="Padres de Familia").count(),
    }

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
        "asistencia_hoy": asistencia_hoy,
        "estudiantes_en_riesgo": estudiantes_en_riesgo,
        "pct_riesgo": pct_riesgo,
        "asistencia_por_mes": asistencia_por_mes,
        "negativos_por_area": negativos_por_area,
        "negativos_semana": negativos_semana,
        "roles_counts": roles_counts,

    }
    return render(request, "dashboard/director_dashboard.html", context)
