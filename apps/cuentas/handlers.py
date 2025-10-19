# apps/cuentas/handlers.py
from django.shortcuts import render

def error_404(request, exception=None):
    previous = (
        request.session.get("cuentas:last_ok_path")
        or request.META.get("HTTP_REFERER")
        or "/"
    )
    ctx = {"previous_url": previous, "seconds": 5}
    return render(request, "errores/404.html", ctx, status=404)  
