from django.contrib.auth.hashers import check_password
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login

from apps.cuentas.models import Usuario

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')  # Puede ser CI o Email
        password = request.POST['password']
        
        # Buscar el usuario por 'ci' o 'email'
        try:
            user = Usuario.objects.get(ci=username)  # Buscar por 'ci'
        except Usuario.DoesNotExist:
            try:
                user = Usuario.objects.get(email=username)  # Buscar por 'email'
            except Usuario.DoesNotExist:
                user = None
        
        if user and user.check_password(password):  # Usar la función check_password
            # Iniciar sesión manualmente
            auth_login(request, user)
            # Redirigir según el rol del usuario
            if user.rol.nombre == "Director":
                return redirect('director_dashboard')
            elif user.rol.nombre == "Regente":
                return redirect('regente_dashboard')
            elif user.rol.nombre == "Secretaria":
                return redirect('secretaria_dashboard')
            elif user.rol.nombre == "Padre de Familia":
                return redirect('padre_dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, "Credenciales inválidas")
    
    return render(request, 'login.html')
