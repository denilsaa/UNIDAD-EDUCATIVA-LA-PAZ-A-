# apps/api/views.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, get_user_model
import json
from json import JSONDecodeError
import traceback

from apps.estudiantes.models import Estudiante, Asistencia
from apps.cursos.models import Curso

Usuario = get_user_model()


# ========== LOGIN ==========
@csrf_exempt
def api_login(request):
    try:
        if request.method != "POST":
            return JsonResponse({"error": "Método no permitido"}, status=405)

        # Leer JSON del body
        try:
            raw_body = (request.body or b"").decode("utf-8")
            data = json.loads(raw_body) if raw_body.strip() else {}
        except JSONDecodeError as e:
            return JsonResponse(
                {"ok": False, "error": f"JSON inválido: {str(e)}"},
                status=400
            )

        ci = data.get("ci")
        password = data.get("password")

        if not ci or not password:
            return JsonResponse(
                {"ok": False, "error": "Faltan campos 'ci' o 'password'"},
                status=400
            )

        user = authenticate(request, username=ci, password=password)

        if user is None:
            return JsonResponse(
                {"ok": False, "error": "Credenciales inválidas"},
                status=400
            )

        # Buscar estudiante relacionado
        # 1) Como hijo (padre_id = user.id)
        estudiante = Estudiante.objects.filter(padre_id=user.id).select_related("curso").first()

        # 2) Como estudiante (ci = user.ci)
        if not estudiante:
            estudiante = Estudiante.objects.filter(ci=getattr(user, "ci", "")).select_related("curso").first()

        nombre_est = ""
        ci_est = ""
        curso_str = ""
        nombre_padre = ""
        ci_padre = ""

        if estudiante:
            nombre_est = f"{estudiante.nombres} {estudiante.apellidos}".strip()
            ci_est = estudiante.ci or ""

            # Padre asociado
            padre = getattr(estudiante, "padre", None)
            if padre:
                nombre_padre = f"{getattr(padre, 'nombres', '')} {getattr(padre, 'apellidos', '')}".strip()
                ci_padre = getattr(padre, "ci", "")
            else:
                # Si no hay padre, usamos el usuario que inició sesión
                nombre_padre = f"{getattr(user, 'nombres', '')} {getattr(user, 'apellidos', '')}".strip()
                ci_padre = getattr(user, "ci", "")

            if estudiante.curso_id and estudiante.curso:
                # AJUSTA ESTOS CAMPOS según tu modelo Curso
                # Por ejemplo: nombre, paralelo, nivel, etc.
                curso_str = str(estudiante.curso)

        else:
            # No se encontró estudiante, pero igual devolvemos datos del usuario
            nombre_padre = f"{getattr(user, 'nombres', '')} {getattr(user, 'apellidos', '')}".strip()
            ci_padre = getattr(user, "ci", "")

        return JsonResponse({
            "ok": True,
            "token": "TOKEN_DE_PRUEBA",
            "nombreEstudiante": nombre_est,
            "ciEstudiante": ci_est,
            "nombrePadre": nombre_padre,
            "ciPadre": ci_padre,
            "curso": curso_str,
        })

    except Exception as e:
        print("ERROR en api_login:")
        print(traceback.format_exc())
        return JsonResponse(
            {"ok": False, "error": f"{type(e).__name__}: {str(e)}"},
            status=500
        )


# ========== PERFIL ==========

def api_perfil(request):
    """
    GET /api/v1/perfil/?ci_estudiante=CI
    Devuelve datos para PerfilController en Unity.
    """
    try:
        ci_estudiante = request.GET.get("ci_estudiante")
        if not ci_estudiante:
            return JsonResponse({"ok": False, "error": "Falta parámetro 'ci_estudiante'"}, status=400)

        estudiante = Estudiante.objects.select_related("curso", "padre").filter(ci=ci_estudiante).first()
        if not estudiante:
            return JsonResponse({"ok": False, "error": "Estudiante no encontrado"}, status=404)

        nombre_est = f"{estudiante.nombres} {estudiante.apellidos}".strip()
        ci_est = estudiante.ci or ""

        padre = getattr(estudiante, "padre", None)
        nombre_padre = ""
        ci_padre = ""
        if padre:
            nombre_padre = f"{getattr(padre, 'nombres', '')} {getattr(padre, 'apellidos', '')}".strip()
            ci_padre = getattr(padre, "ci", "")

        curso_str = ""
        if estudiante.curso_id and estudiante.curso:
            curso_str = str(estudiante.curso)

        return JsonResponse({
            "ok": True,
            "nombreEstudiante": nombre_est,
            "ciEstudiante": ci_est,
            "nombrePadre": nombre_padre,
            "ciPadre": ci_padre,
            "curso": curso_str,
        })

    except Exception as e:
        print("ERROR en api_perfil:")
        print(traceback.format_exc())
        return JsonResponse(
            {"ok": False, "error": f"{type(e).__name__}: {str(e)}"},
            status=500
        )


# ========== ASISTENCIA ==========

def api_asistencia(request):
    """
    GET /api/v1/asistencia/?ci_estudiante=CI
    Devuelve la lista de asistencias del estudiante.
    """
    try:
        ci_estudiante = request.GET.get("ci_estudiante")
        if not ci_estudiante:
            return JsonResponse({"ok": False, "error": "Falta parámetro 'ci_estudiante'"}, status=400)

        estudiante = Estudiante.objects.filter(ci=ci_estudiante).first()
        if not estudiante:
            return JsonResponse({"ok": False, "error": "Estudiante no encontrado"}, status=404)

        asistencias = Asistencia.objects.filter(estudiante_id=estudiante.id).order_by("fecha")

        items = []
        for a in asistencias:
            fecha_str = a.fecha.strftime("%d/%m/%Y") if a.fecha else ""
            items.append({
                "fecha": fecha_str,
                "estado": a.estado,  # "Presente", "Falta", "Atraso"
            })

        return JsonResponse({
            "ok": True,
            "items": items,
        })

    except Exception as e:
        print("ERROR en api_asistencia:")
        print(traceback.format_exc())
        return JsonResponse(
            {"ok": False, "error": f"{type(e).__name__}: {str(e)}"},
            status=500
        )
# ========== KÁRDEX ==========

def api_kardex(request):
    """
    GET /api/v1/kardex/?ci_estudiante=CI
    Devuelve registros del kárdex del estudiante
    """
    try:
        ci_estudiante = request.GET.get("ci_estudiante")
        if not ci_estudiante:
            return JsonResponse({"ok": False, "error": "Falta parámetro 'ci_estudiante'"}, status=400)

        estudiante = Estudiante.objects.filter(ci=ci_estudiante).first()
        if not estudiante:
            return JsonResponse({"ok": False, "error": "Estudiante no encontrado"}, status=404)

        registros = estudiante.kardex_registros.all().order_by("-fecha")

        items = []
        for r in registros:
            items.append({
                "fecha": r.fecha.strftime("%d/%m/%Y"),
                "detalle": r.detalle,
                "puntos": r.puntos,
            })

        return JsonResponse({"ok": True, "items": items})

    except Exception as e:
        print("ERROR en api_kardex", e)
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
