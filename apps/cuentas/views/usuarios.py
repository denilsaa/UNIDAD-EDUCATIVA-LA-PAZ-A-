# apps/cuentas/views/usuarios.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST

from apps.cuentas.models import Usuario
from apps.cuentas.forms import UsuarioCreateForm, UsuarioUpdateForm

# ⬇️ Decorador que exige login y rol == director
from apps.cuentas.decorators import role_required
from apps.estudiantes.models.estudiante import Estudiante


@role_required("director")
def lista_usuarios(request):
    usuarios = Usuario.objects.all().order_by("-id")
    return render(request, "cuentas/lista_usuarios.html", {"usuarios": usuarios})


@role_required("director")
def ver_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    return render(request, "cuentas/ver_usuario.html", {"usuario": usuario})


@role_required("director")
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


@role_required("director")
def editar_usuario(request, user_id):
    """
    Vista que permite al director editar un usuario.
    """
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


@role_required("director")
def eliminar_usuario(request, user_id):
    """
    Vista que permite eliminar completamente un usuario.
    Si el usuario tiene estudiantes asignados (como padre o regente), se pide confirmación adicional.
    """
    usuario = get_object_or_404(Usuario, id=user_id)

    # 🔹 Estudiantes asociados si es padre
    estudiantes_padre = Estudiante.objects.filter(padre=usuario)

    # 🔹 Estudiantes asociados si es regente
    estudiantes_regente = Estudiante.objects.filter(curso__regente=usuario)

    # 🔹 Combinar ambos QuerySets en uno solo (sin duplicados)
    estudiantes_asociados = (estudiantes_padre | estudiantes_regente).distinct()

    if request.method == "POST":
        if "eliminar_todo" in request.POST:
            estudiantes_asociados.delete()
            usuario.delete()
            messages.success(
                request,
                f"🗑️ El usuario {usuario} y sus estudiantes fueron eliminados permanentemente."
            )
            return redirect("cuentas:lista_usuarios")

        elif not estudiantes_asociados.exists():
            usuario.delete()
            messages.success(
                request,
                f"🗑️ El usuario {usuario} fue eliminado permanentemente."
            )
            return redirect("cuentas:lista_usuarios")

        return redirect("cuentas:lista_usuarios")

    # Si es GET, mostrar la confirmación
    return render(
        request,
        "cuentas/eliminar_usuario.html",
        {"usuario": usuario, "estudiantes": estudiantes_asociados}
    )


from django.http import JsonResponse

#  Nueva vista para verificar CI en tiempo real
@role_required("director")
def verificar_ci(request):
    ci = request.GET.get("ci", "")
    existe = Usuario.objects.filter(ci=ci).exists()
    return JsonResponse({"existe": existe})
