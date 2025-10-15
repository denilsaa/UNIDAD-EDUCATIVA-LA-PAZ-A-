# En cuentas/views/director_dashboard.py

from django.shortcuts import render
from apps.cuentas.models import Usuario

def director_dashboard(request):
    # Obtener todos los usuarios
    usuarios = Usuario.objects.all()
    
    # Obtener conteo de usuarios por rol
    director_count = Usuario.objects.filter(rol__nombre='Director').count()
    regente_count = Usuario.objects.filter(rol__nombre='Regente').count()
    secretaria_count = Usuario.objects.filter(rol__nombre='Secretaria').count()
    padre_count = Usuario.objects.filter(rol__nombre='Padre de Familia').count()

    return render(request, 'dashboard/director_dashboard.html', {
        'usuarios': usuarios,
        'director_count': director_count,
        'regente_count': regente_count,
        'secretaria_count': secretaria_count,
        'padre_count': padre_count
    })
