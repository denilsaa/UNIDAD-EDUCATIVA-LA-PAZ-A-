# apps/cuentas/views/usuarios.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db import IntegrityError

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
            try:
                form.save()
            except IntegrityError:
                form.add_error('email', "Este correo ya está registrado.")
                return render(request, "cuentas/crear_usuario.html", {"form": form})
            messages.success(request, "Usuario creado correctamente.")
            return redirect("cuentas:lista_usuarios")
    else:
        form = UsuarioCreateForm()
    return render(request, "cuentas/crear_usuario.html", {"form": form})


@role_required("director")
def editar_usuario(request, user_id):
    """
    Vista que permite al director editar un usuario.
    🚫 Si el director edita SU PROPIO usuario, no puede marcarse como inactivo.
    """
    usuario = get_object_or_404(Usuario, id=user_id)
    es_autoedicion = (usuario.id == request.user.id)

    if request.method == "POST":
        # Carga del form
        form = UsuarioUpdateForm(request.POST, instance=usuario)

        # Defensa fuerte: si intenta inactivarse a sí mismo, rechazar
        if es_autoedicion:
            # Si el campo viene desmarcado (False), bloquear
            is_activo_nuevo = form.data.get("is_activo")
            # En forms con checkbox, que venga None/ausente equivale a False
            quiere_inactivarse = not bool(is_activo_nuevo)
            if quiere_inactivarse:
                messages.error(request, "No puedes inactivarte a ti mismo.")
                # Mantener el valor actual en BD (True) y re-render con el field deshabilitado
                form = UsuarioUpdateForm(instance=usuario)
                if "is_activo" in form.fields:
                    form.fields["is_activo"].disabled = True
                    form.fields["is_activo"].help_text = "No puedes inactivarte a ti mismo."
                return render(request, "cuentas/editar_usuario.html", {"form": form, "usuario": usuario, "es_autoedicion": es_autoedicion})

        if form.is_valid():
            # Salvaguarda extra por si algún caso borde pasara validación
            if es_autoedicion and (not form.cleaned_data.get("is_activo", True)):
                messages.error(request, "No puedes inactivarte a ti mismo.")
                return redirect("cuentas:lista_usuarios")

            form.save()
            messages.success(request, "Usuario actualizado correctamente.")
            return redirect("cuentas:lista_usuarios")
    else:
        form = UsuarioUpdateForm(instance=usuario)
        # UX: deshabilitar el checkbox de activo al editarte a ti mismo
        if es_autoedicion and "is_activo" in form.fields:
            form.fields["is_activo"].disabled = True
            form.fields["is_activo"].help_text = "No puedes inactivarte a ti mismo."

    return render(
        request,
        "cuentas/editar_usuario.html",
        {"form": form, "usuario": usuario, "es_autoedicion": es_autoedicion},
    )


@role_required("director")
def eliminar_usuario(request, user_id):
    """
    Vista que permite eliminar completamente un usuario.
    Si el usuario tiene estudiantes asignados (como padre o regente), se pide confirmación adicional.
    🚫 Un director NO puede eliminarse a sí mismo.
    """
    usuario = get_object_or_404(Usuario, id=user_id)

    # 🚫 Evitar auto-eliminación (defensa principal en back-end)
    if usuario.id == request.user.id:
        messages.error(request, "No puedes eliminarte a ti mismo.")
        return redirect("cuentas:lista_usuarios")

    # 🔹 Estudiantes asociados si es padre
    estudiantes_padre = Estudiante.objects.filter(padre=usuario)

    # 🔹 Estudiantes asociados si es regente
    estudiantes_regente = Estudiante.objects.filter(curso__regente=usuario)

    # 🔹 Combinar ambos QuerySets en uno solo (sin duplicados)
    estudiantes_asociados = (estudiantes_padre | estudiantes_regente).distinct()

    if request.method == "POST":
        # Doble-check por si cambió el contexto (defensa extra)
        if usuario.id == request.user.id:
            messages.error(request, "No puedes eliminarte a ti mismo.")
            return redirect("cuentas:lista_usuarios")

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


#  Nueva vista para verificar CI en tiempo real
@role_required("director")
def verificar_ci(request):
    ci = request.GET.get("ci", "")
    existe = Usuario.objects.filter(ci=ci).exists()
    return JsonResponse({"existe": existe})
