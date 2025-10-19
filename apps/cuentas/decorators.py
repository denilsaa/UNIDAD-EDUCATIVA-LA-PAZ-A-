from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
# (opcional) también puedes usar: from django.core.exceptions import PermissionDenied

def role_required(*roles):
    def decorator(viewfunc):
        @wraps(viewfunc)
        @login_required
        def _wrapped(request, *args, **kwargs):
            # get role name safely
            rol_nombre = (getattr(getattr(request.user, "rol", None), "nombre", "") or "").lower()
            if any(r in rol_nombre for r in roles):
                return viewfunc(request, *args, **kwargs)
            # ❌ No autorizado -> render 403 con tu template (incluye el JS de 5s)
            return render(request, "403.html", status=403)
            # Alternativa:
            # raise PermissionDenied
        return _wrapped
    return decorator
