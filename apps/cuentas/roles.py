# apps/cuentas/roles.py
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
