# apps/cuentas/views_dev.py
from django.shortcuts import render

def dev_404(request):
    """
    Vista solo para desarrollo (DEBUG=True).
    Renderiza la misma plantilla del 404 con contador y 'previous_url'.
    """
    previous = (
        request.session.get("cuentas:last_ok_path")
        or request.META.get("HTTP_REFERER")
        or "/"
    )
    ctx = {"previous_url": previous, "seconds": 5}
    return render(request, "errores/404.html", ctx, status=200)  # status 200 para que cargue assets
