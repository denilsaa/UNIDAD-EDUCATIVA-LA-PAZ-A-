from functools import wraps
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required

def _rol_nombre(user) -> str:
    return (getattr(getattr(user, "rol", None), "nombre", "") or "").lower()

def _has_any_role(user, roles) -> bool:
    r = _rol_nombre(user)
    return any(role in r for role in roles)

def role_required(*roles):
    def decorator(viewfunc):
        @wraps(viewfunc)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if _has_any_role(request.user, roles):
                return viewfunc(request, *args, **kwargs)
            return HttpResponseForbidden("No autorizado.")
        return _wrapped
    return decorator
