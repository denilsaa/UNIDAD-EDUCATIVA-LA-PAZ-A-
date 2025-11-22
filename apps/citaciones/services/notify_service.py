# apps/citaciones/services/notify_service.py
from typing import List
from apps.cuentas.roles import es_padre as es_rol_padre


def _es_usuario_padre(u) -> bool:
    """
    Devuelve True si el usuario tiene un rol de padre y está activo.

    Usa apps.cuentas.roles.es_padre, que funciona aunque el rol se llame
    'Padre', 'Padre de familia', etc. (porque busca el texto 'padre').
    """
    try:
        return es_rol_padre(u) and getattr(u, "is_activo", False)
    except Exception:
        return False


def resolve_padres_ids(estudiante) -> List[int]:
    """
    Devuelve los IDs de usuarios que deben recibir notificaciones de este
    estudiante. Adaptado a tu modelo actual:

      Estudiante.padre -> Usuario  (rol: 'Padre de familia')
    """
    if estudiante is None:
        return []

    ids: set[int] = set()

    # 1) FK directo: Estudiante.padre
    try:
        u = getattr(estudiante, "padre", None)
        if u and _es_usuario_padre(u):
            ids.add(u.id)
    except Exception:
        pass

    # 2) Si en algún momento usas M2M padres/usuarios, también los tomamos
    for attr in ("padres", "usuarios"):
        try:
            rel = getattr(estudiante, attr, None)
            if rel is not None:
                for u in rel.all():
                    if _es_usuario_padre(u):
                        ids.add(u.id)
        except Exception:
            pass

    # 3) Otros posibles nombres de FK (por si los usas en el futuro)
    for attr in ("apoderado", "tutor", "tutor_principal", "tutor_secundario"):
        try:
            u = getattr(estudiante, attr, None)
            if u and _es_usuario_padre(u):
                ids.add(u.id)
        except Exception:
            pass

    return list(ids)
