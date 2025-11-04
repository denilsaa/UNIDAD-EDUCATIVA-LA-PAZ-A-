# apps/citaciones/services/notify_service.py
from typing import List
from django.apps import apps

def _es_usuario_padre(u) -> bool:
    try:
        rol = getattr(u, "rol", None)
        nombre = (getattr(rol, "nombre", "") or "").strip().lower()
        return bool(nombre == "padre" and getattr(u, "is_activo", False))
    except Exception:
        return False

def resolve_padres_ids(estudiante) -> List[int]:
    """
    Devuelve los user_id de los padres/tutores que deben recibir notificación.
    Está escrito para 'adivinar' tu modelo sin romper si falta algo.
    Ajusta este método a tu esquema real cuando lo tengas claro.
    """
    if estudiante is None:
        return []

    ids = set()

    # 1) M2M clásico: estudiante.padres (-> Usuario)
    try:
        padres_m2m = getattr(estudiante, "padres", None)
        if padres_m2m is not None:
            for u in padres_m2m.all():
                if _es_usuario_padre(u):
                    ids.add(u.id)
    except Exception:
        pass

    # 2) Reverse M2M/related_name: estudiante.usuarios (si lo usas así)
    try:
        usuarios_rel = getattr(estudiante, "usuarios", None)
        if usuarios_rel is not None:
            for u in usuarios_rel.all():
                if _es_usuario_padre(u):
                    ids.add(u.id)
    except Exception:
        pass

    # 3) Atributos FK comunes en escuelas: apoderado / tutor_*  (si existen)
    for attr in ("apoderado", "tutor", "tutor_principal", "tutor_secundario"):
        try:
            u = getattr(estudiante, attr, None)
            if u and _es_usuario_padre(u):
                ids.add(u.id)
        except Exception:
            pass

    # 4) Si tenías emails/teléfonos y un modelo intermedio (muy opcional):
    #    puedes mapearlos a Usuario aquí si es necesario.

    return list(ids)
