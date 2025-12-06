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

        # ... (autenticación previa igual) ...
        user = authenticate(request, username=ci, password=password)

        if user is None:
            return JsonResponse({"ok": False, "error": "Credenciales inválidas"}, status=400)

        # Determinar ROL
        from apps.cuentas.roles import es_padre, es_regente, es_director
        
        rol_str = "padre" # Default
        if es_regente(user):
            rol_str = "regente"
        elif es_director(user):
            rol_str = "director"
        
        # Datos comunes
        resp_data = {
            "ok": True,
            "token": "TOKEN_DE_PRUEBA",
            "rol": rol_str,
            "usuario_nombre": f"{user.nombres} {user.apellidos}".strip(),
            "usuario_ci": user.ci,
            "usuario_id": user.id,  # Required for WebSocket notifications
        }

        # Lógica por ROL
        if rol_str == "regente":
            # Obtener cursos asignados
            cursos = Curso.objects.filter(regente_id=user.id).order_by("nivel", "paralelo")
            lista_cursos = []
            for c in cursos:
                lista_cursos.append({
                    "id": c.id,
                    "nombre": str(c), # "1ro Secundaria A"
                    "nivel": c.nivel,
                    "paralelo": c.paralelo
                })
            resp_data["cursos"] = lista_cursos
        
        else:
            # Asumimos PADRE (o estudiante directo)
            # Buscar TODOS los hijos
            hijos = Estudiante.objects.filter(padre_id=user.id).select_related("curso")
            
            # Si no tiene hijos asignados, ver si es estudiante él mismo
            if not hijos.exists():
                hijos = Estudiante.objects.filter(ci=user.ci).select_related("curso")

            lista_hijos = []
            for h in hijos:
                curso_nom = str(h.curso) if h.curso else "Sin curso"
                lista_hijos.append({
                    "ci": h.ci,
                    "nombre_completo": f"{h.nombres} {h.apellidos}".strip(),
                    "curso": curso_nom,
                    "id": h.id
                })
            
            resp_data["hijos"] = lista_hijos
            
            # Mantener compatibilidad con app vieja (primer hijo)
            if lista_hijos:
                h1 = lista_hijos[0]
                resp_data["nombreEstudiante"] = h1["nombre_completo"]
                resp_data["ciEstudiante"] = h1["ci"]
                resp_data["curso"] = h1["curso"]
            else:
                resp_data["nombreEstudiante"] = resp_data["usuario_nombre"]
                resp_data["ciEstudiante"] = resp_data["usuario_ci"]
                resp_data["curso"] = ""

        return JsonResponse(resp_data)

    except Exception as e:
        print("ERROR en api_login:")
        print(traceback.format_exc())
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


# ========== CITACIONES ==========
from apps.citaciones.models.citacion import Citacion

def api_citaciones(request):
    """
    GET /api/v1/citaciones/?ci_estudiante=...
    """
    try:
        ci_estudiante = request.GET.get("ci_estudiante")
        if not ci_estudiante:
             return JsonResponse({"ok": False, "error": "Falta ci_estudiante"}, status=400)
        
        estudiante = Estudiante.objects.filter(ci=ci_estudiante).first()
        if not estudiante:
            return JsonResponse({"ok": False, "error": "Estudiante no encontrado"}, status=404)

        citaciones = Citacion.objects.filter(estudiante=estudiante).order_by("-creado_en")
        
        items = []
        for c in citaciones:
            fecha_str = ""
            if c.fecha_citacion:
                fecha_str = c.fecha_citacion.strftime("%d/%m/%Y")
                if c.hora_citacion:
                    fecha_str += f" {c.hora_citacion.strftime('%H:%M')}"
            
            items.append({
                "id": c.id,
                "motivo": c.motivo_resumen,
                "estado": c.estado, # ABIERTA, AGENDADA, etc.
                "fecha": fecha_str,
                "creado_en": c.creado_en.strftime("%d/%m/%Y")
            })
            
        return JsonResponse({"ok": True, "items": items})

    except Exception as e:
        print("ERROR api_citaciones:", e)
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


# ========== REGENTE: ASISTENCIA ==========
@csrf_exempt
def api_regente_asistencia(request):
    """
    POST /api/v1/regente/asistencia/
    Body: { "fecha": "YYYY-MM-DD", "asistencias": [ {"ci": "...", "estado": "..."} ] }
    """
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body)
        fecha_str = data.get("fecha")
        asistencias = data.get("asistencias", [])

        if not fecha_str or not asistencias:
            return JsonResponse({"ok": False, "error": "Faltan datos (fecha o asistencias)"}, status=400)

        # Validar fecha
        from datetime import datetime
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()

        creados = 0
        actualizados = 0
        errores = []

        for item in asistencias:
            ci = item.get("ci")
            estado = item.get("estado") # PRESENTE, FALTA, ATRASO
            
            estudiante = Estudiante.objects.filter(ci=ci).first()
            if not estudiante:
                errores.append(f"CI {ci} no encontrado")
                continue

            # Crear o Actualizar
            obj, created = Asistencia.objects.update_or_create(
                estudiante=estudiante,
                fecha=fecha,
                defaults={"estado": estado}
            )
            
            if created:
                creados += 1
            else:
                actualizados += 1

        return JsonResponse({
            "ok": True,
            "creados": creados,
            "actualizados": actualizados,
            "errores": errores
        })

    except Exception as e:
        print("ERROR api_regente_asistencia:", e)
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


# ========== REGENTE: KÁRDEX ==========
from apps.estudiantes.models.kardex_registro import KardexRegistro
from apps.estudiantes.models.kardex_item import KardexItem

@csrf_exempt
def api_regente_kardex(request):
    """
    POST /api/v1/regente/kardex/
    Body: { "ci_estudiante": "...", "item_id": 1, "observacion": "..." }
    """
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body)
        ci = data.get("ci_estudiante")
        item_id = data.get("item_id")
        observacion = data.get("observacion", "")
        
        # Opcional: ID del docente/regente que reporta (si se envía en el body o se saca del token/session)
        # Por simplicidad, asumimos que el backend podría sacarlo del user autenticado si usáramos tokens reales.
        # Aquí lo dejaremos null o lo pasaremos si la app lo envía.
        
        estudiante = Estudiante.objects.filter(ci=ci).first()
        if not estudiante:
            return JsonResponse({"ok": False, "error": "Estudiante no encontrado"}, status=404)

        kardex_item = KardexItem.objects.filter(id=item_id).first()
        if not kardex_item:
            return JsonResponse({"ok": False, "error": "Ítem de kárdex no encontrado"}, status=404)

        from datetime import date
        registro = KardexRegistro.objects.create(
            estudiante=estudiante,
            kardex_item=kardex_item,
            fecha=date.today(),
            observacion=observacion,
            # docente=request.user # Si estuviera autenticado con session
        )

        return JsonResponse({"ok": True, "id": registro.id})

        return JsonResponse({"ok": True, "id": registro.id})

    except Exception as e:
        print("ERROR api_regente_kardex:", e)
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


# ========== REGENTE: DATOS AUXILIARES ==========

def api_estudiantes_curso(request):
    """
    GET /api/v1/estudiantes-curso/?curso_id=...
    """
    try:
        curso_id = request.GET.get("curso_id")
        if not curso_id:
            return JsonResponse({"ok": False, "error": "Falta curso_id"}, status=400)

        estudiantes = Estudiante.objects.filter(curso_id=curso_id).order_by("apellidos", "nombres")
        
        data = []
        for e in estudiantes:
            data.append({
                "ci": e.ci,
                "nombre": f"{e.nombres} {e.apellidos}".strip(),
                "id": e.id
            })
            
        return JsonResponse({"ok": True, "estudiantes": data})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


def api_kardex_items(request):
    """
    GET /api/v1/kardex-items/
    """
    try:
        items = KardexItem.objects.filter(activo=True).order_by("area", "descripcion")
        data = []
        for i in items:
            # Calculamos puntos (peso * sentido)
            puntos = i.peso if i.sentido == KardexItem.Sentido.POSITIVO else -i.peso
            
            data.append({
                "id": i.id,
                "descripcion": i.descripcion,
                "area": i.area,
                "puntos": puntos
            })
            
        return JsonResponse({"ok": True, "items": data})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)




# ========== PERFIL ==========

def api_perfil(request):
    """
    GET /api/v1/perfil/?ci_estudiante=CI  (o ?ci=CI)
    """
    try:
        # Aceptar ambos nombres: ci_estudiante y ci
        ci_estudiante = request.GET.get("ci_estudiante") or request.GET.get("ci")
        if not ci_estudiante:
            return JsonResponse(
                {"ok": False, "error": "Falta parámetro 'ci' o 'ci_estudiante'"},
                status=400
            )

        estudiante = Estudiante.objects.select_related("curso", "padre").filter(ci=ci_estudiante).first()

        if not estudiante:
            # Fallback de DEMO para que la app no reviente si no hay estudiante
            return JsonResponse({
                "ok": True,
                "nombreEstudiante": "Estudiante Demo",
                "ciEstudiante": ci_estudiante,
                "nombrePadre": "Padre Demo",
                "ciPadre": "",
                "curso": "6to de Secundaria"
            })

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
    GET /api/v1/asistencia/?ci_estudiante=CI  (o ?ci=CI)
    Devuelve la lista de asistencias del estudiante.
    """
    try:
        # Aceptar ambos nombres
        ci_estudiante = request.GET.get("ci_estudiante") or request.GET.get("ci")
        if not ci_estudiante:
            return JsonResponse(
                {"ok": False, "error": "Falta parámetro 'ci' o 'ci_estudiante'"},
                status=400
            )

        estudiante = Estudiante.objects.filter(ci=ci_estudiante).first()

        if not estudiante:
            # DEMO: si no hay estudiante con ese CI, devolver datos de ejemplo
            items = [
                {"fecha": "01/11/2025", "estado": "Presente"},
                {"fecha": "02/11/2025", "estado": "Falta"},
                {"fecha": "03/11/2025", "estado": "Atraso"},
            ]
            return JsonResponse({"ok": True, "items": items})

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

        registros = estudiante.kardex_registros.select_related('kardex_item').all().order_by("-fecha")

        items = []
        for r in registros:
            # Construir detalle con descripción del item + observación opcional
            detalle = r.kardex_item.descripcion
            if r.observacion:
                detalle += f" ({r.observacion})"

            items.append({
                "fecha": r.fecha.strftime("%d/%m/%Y"),
                "detalle": detalle,
                "puntos": r.kardex_item.peso,
            })

        return JsonResponse({"ok": True, "items": items})

    except Exception as e:
        print("ERROR en api_kardex", e)
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


