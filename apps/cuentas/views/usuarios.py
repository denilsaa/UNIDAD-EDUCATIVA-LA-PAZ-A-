# apps/cuentas/views/usuarios.py
from django.shortcuts import render, get_object_or_404, redirect
from apps.cuentas.models import Usuario
from apps.cuentas.forms import UsuarioCreateForm, UsuarioUpdateForm
from django.contrib import messages

def crear_usuario(request):
    if request.method == "POST":
        form = UsuarioCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario creado correctamente.")
            return redirect("cuentas:lista_usuarios")
    else:
        form = UsuarioCreateForm()
    return render(request, "cuentas/crear_usuario.html", {"form": form})

def lista_usuarios(request):
    usuarios = Usuario.objects.all().order_by("-id")
    return render(request, "cuentas/lista_usuarios.html", {"usuarios": usuarios})

def ver_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    return render(request, "cuentas/ver_usuario.html", {"usuario": usuario})

def editar_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    if request.method == "POST":
        form = UsuarioUpdateForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario actualizado correctamente.")
            return redirect("cuentas:lista_usuarios")
    else:
        form = UsuarioUpdateForm(instance=usuario)
    return render(request, "cuentas/editar_usuario.html", {"form": form, "usuario": usuario})

def eliminar_usuario(request, user_id):
    # borrado lógico
    usuario = get_object_or_404(Usuario, id=user_id)
    usuario.is_activo = False
    usuario.save()
    messages.info(request, "Usuario marcado como inactivo.")
    return redirect("cuentas:lista_usuarios")
