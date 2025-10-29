from django.contrib.auth import get_user_model

def rol_nombre(user) -> str:
    return (getattr(getattr(user, "rol", None), "nombre", "") or "").lower()

def has_any_role(user, *roles) -> bool:
    r = rol_nombre(user)
    return any(role in r for role in roles)

def es_director(user) -> bool:
    return has_any_role(user, "director")

def es_regente(user) -> bool:
    return has_any_role(user, "regente")

def es_secretaria(user) -> bool:
    return has_any_role(user, "secretaria", "secretaría")

def es_padre(user) -> bool:
    return has_any_role(user, "padre")

def total_directores_activos(exclude_pk=None) -> int:
    Usuario = get_user_model()
    qs = Usuario.objects.filter(is_activo=True)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    # ✅ llamar es_director directamente, sin import
    return sum(1 for u in qs.select_related("rol") if es_director(u))
