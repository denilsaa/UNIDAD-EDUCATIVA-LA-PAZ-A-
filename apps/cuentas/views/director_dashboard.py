# apps/cuentas/views/director_dashboard.py

from django.shortcuts import render

def director_dashboard(request):
    # Renderizar la plantilla correspondiente para el dashboard del director
    return render(request, 'dashboard/director_dashboard.html')
