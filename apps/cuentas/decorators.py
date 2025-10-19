from functools import wraps
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from .roles import has_any_role

def role_required(*roles):
    def decorator(viewfunc):
        @wraps(viewfunc)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if has_any_role(request.user, *roles):
                return viewfunc(request, *args, **kwargs)
            return HttpResponseForbidden("No autorizado.")
        return _wrapped
    return decorator
