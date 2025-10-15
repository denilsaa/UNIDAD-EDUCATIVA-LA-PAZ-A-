# En cuentas/views/usuarios.py

from django.shortcuts import render, get_object_or_404, redirect
from apps.cuentas.models import Usuario
from apps.cuentas.forms import UsuarioForm

# Vista para crear un nuevo usuario
def crear_usuario(request):
    if request.method == "POST":
        form = UsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('cuentas:lista_usuarios')  # Redirige al listado después de crear
    else:
        form = UsuarioForm()
    return render(request, 'cuentas/crear_usuario.html', {'form': form})

# Vista para listar todos los usuarios
def lista_usuarios(request):
    usuarios = Usuario.objects.all()
    return render(request, 'cuentas/lista_usuarios.html', {'usuarios': usuarios})

# Vista para ver los detalles de un usuario
def ver_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    return render(request, 'cuentas/ver_usuario.html', {'usuario': usuario})

# Vista para editar un usuario existente
def editar_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            return redirect('cuentas:lista_usuarios')
    else:
        form = UsuarioForm(instance=usuario)
    return render(request, 'cuentas/editar_usuario.html', {'form': form})

# Vista para eliminar (desactivar) un usuario
def eliminar_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    usuario.is_activo = False  # Marcamos al usuario como inactivo
    usuario.save()
    return redirect('cuentas:lista_usuarios')
