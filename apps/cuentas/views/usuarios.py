# apps/cuentas/views/usuarios.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError

from apps.cuentas.models import Usuario
from apps.cuentas.forms import UsuarioCreateForm, UsuarioUpdateForm

# 🔒 Decorador que exige login y rol == director
from apps.cuentas.decorators import role_required
from apps.cuentas.roles import es_director, total_directores_activos
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
@require_http_methods(["GET", "POST"])
def crear_usuario(request):
    if request.method == "POST":
        form = UsuarioCreateForm(request.POST)
        if form.is_valid():
            try:
                form.save()
            except IntegrityError:
                form.add_error("email", "Este correo ya está registrado.")
                return render(request, "cuentas/crear_usuario.html", {"form": form})
            messages.success(request, "Usuario creado correctamente.")
            return redirect("cuentas:lista_usuarios")
    else:
        form = UsuarioCreateForm()
    return render(request, "cuentas/crear_usuario.html", {"form": form})


@role_required("director")
@require_http_methods(["GET", "POST"])
@transaction.atomic
def editar_usuario(request, user_id):
    """
    Edita un usuario. Reglas:
    - Si es autoedición, no puede inactivarse a sí mismo.
    - Si el usuario editado es el ÚLTIMO Director activo, no se puede cambiar su rol ni inactivarlo.
      (Los campos se deshabilitan en el formulario y además se valida al guardar).
    - Cualquier intento que viole las señales muestra mensaje y no causa 500.
    """
    # Bloqueo de fila para evitar condiciones de carrera
    usuario = get_object_or_404(Usuario.objects.select_for_update(), id=user_id)
    es_autoedicion = (usuario.id == request.user.id)

    if request.method == "POST":
        form = UsuarioUpdateForm(request.POST, instance=usuario)

        # Defensa UX/seguridad: si es autoedición, no permitir desactivarse
        if es_autoedicion:
            # Checkbox ausente => False
            quiere_inactivarse = not bool(request.POST.get("is_activo"))
            if quiere_inactivarse:
                messages.error(request, "No puedes inactivarte a ti mismo.")
                # Re-render con el campo deshabilitado para mayor claridad
                form = UsuarioUpdateForm(instance=usuario)
                if "is_activo" in form.fields:
                    form.fields["is_activo"].disabled = True
                    form.fields["is_activo"].help_text = "No puedes inactivarte a ti mismo."
                return render(
                    request,
                    "cuentas/editar_usuario.html",
                    {"form": form, "usuario": usuario, "es_autoedicion": es_autoedicion},
                )

        if form.is_valid():
            # Reglas de último Director (por si alguien manipula el DOM)
            es_director_actual = es_director(usuario)
            es_ultimo_director = es_director_actual and total_directores_activos(exclude_pk=usuario.pk) == 0

            # Valores “nuevos” propuestos
            nuevo_rol = form.cleaned_data.get("rol") if "rol" in form.cleaned_data else getattr(usuario, "rol", None)
            nuevo_is_activo = form.cleaned_data.get("is_activo", getattr(usuario, "is_activo", True))

            # ¿Con el nuevo rol seguiría siendo director?
            sigue_si_endir = (getattr(nuevo_rol, "nombre", "") or "").strip().lower() == "director"

            if es_ultimo_director:
                # No puede perder rol de Director ni desactivarse
                if not sigue_si_endir:
                    form.add_error("rol", "No puedes cambiar el rol del único Director activo.")
                    messages.error(request, "No puedes cambiar el rol del único Director activo.")
                    return render(
                        request,
                        "cuentas/editar_usuario.html",
                        {"form": form, "usuario": usuario, "es_autoedicion": es_autoedicion},
                    )
                if not nuevo_is_activo:
                    if "is_activo" in form.fields:
                        form.add_error("is_activo", "No puedes desactivar al único Director activo.")
                    messages.error(request, "No puedes desactivar al único Director activo.")
                    return render(
                        request,
                        "cuentas/editar_usuario.html",
                        {"form": form, "usuario": usuario, "es_autoedicion": es_autoedicion},
                    )

            # Guardar con manejo de ValidationError de señales
            try:
                form.save()  # Las señales vuelven a validar (capa de seguridad)
                messages.success(request, "Usuario actualizado correctamente.")
                return redirect("cuentas:lista_usuarios")
            except ValidationError as e:
                msg = getattr(e, "message", str(e))
                # Añadir error a un campo si aplica
                if "Director" in msg or "Director" in str(nuevo_rol):
                    if "rol" in form.fields:
                        form.add_error("rol", msg)
                else:
                    form.add_error(None, msg)
                messages.error(request, msg)
                # Re-render con errores
                return render(
                    request,
                    "cuentas/editar_usuario.html",
                    {"form": form, "usuario": usuario, "es_autoedicion": es_autoedicion},
                )
    else:
        form = UsuarioUpdateForm(instance=usuario)

        # UX: si es último director, deshabilitar campos de riesgo
        if es_director(usuario) and total_directores_activos(exclude_pk=usuario.pk) == 0:
            if "rol" in form.fields:
                form.fields["rol"].disabled = True
                form.fields["rol"].help_text = "No puedes cambiar el rol: es el único Director activo."
            if "is_activo" in form.fields:
                form.fields["is_activo"].disabled = True
                form.fields["is_activo"].help_text = "No puedes desactivarlo: es el único Director activo."

        # UX: si es autoedición, no permitir desactivarse
        if es_autoedicion and "is_activo" in form.fields:
            form.fields["is_activo"].disabled = True
            form.fields["is_activo"].help_text = "No puedes inactivarte a ti mismo."

    return render(
        request,
        "cuentas/editar_usuario.html",
        {"form": form, "usuario": usuario, "es_autoedicion": es_autoedicion},
    )


@role_required("director")
@require_http_methods(["GET", "POST"])
@transaction.atomic
def eliminar_usuario(request, user_id):
    """
    Elimina un usuario con confirmación.
    Reglas:
    - Un director NO puede eliminarse a sí mismo.
    - No se puede eliminar al ÚLTIMO Director activo (señales + manejo de error).
    - Si tiene estudiantes asociados (como padre o regente), se requiere confirmación extra.
    """
    usuario = get_object_or_404(Usuario.objects.select_for_update(), id=user_id)

    # 🚫 Evitar auto-eliminación
    if usuario.id == request.user.id:
        messages.error(request, "No puedes eliminarte a ti mismo.")
        return redirect("cuentas:lista_usuarios")

    # 🔹 Estudiantes asociados si es padre
    estudiantes_padre = Estudiante.objects.filter(padre=usuario)
    # 🔹 Estudiantes asociados si es regente
    estudiantes_regente = Estudiante.objects.filter(curso__regente=usuario)
    # 🔹 Unir
    estudiantes_asociados = (estudiantes_padre | estudiantes_regente).distinct()

    if request.method == "POST":
        # Segunda defensa contra auto-eliminación por si el contexto cambió
        if usuario.id == request.user.id:
            messages.error(request, "No puedes eliminarte a ti mismo.")
            return redirect("cuentas:lista_usuarios")

        try:
            if "eliminar_todo" in request.POST:
                estudiantes_asociados.delete()
                usuario.delete()  # Señales saltan si es último Director
                messages.success(
                    request,
                    f"🗑️ El usuario {usuario} y sus estudiantes fueron eliminados permanentemente."
                )
                return redirect("cuentas:lista_usuarios")

            elif not estudiantes_asociados.exists():
                usuario.delete()  # Señales validan
                messages.success(
                    request,
                    f"🗑️ El usuario {usuario} fue eliminado permanentemente."
                )
                return redirect("cuentas:lista_usuarios")

            # Si tenía estudiantes y no se marcó eliminar_todo, no hacemos nada
            return redirect("cuentas:lista_usuarios")

        except ValidationError as e:
            # Si es el último Director, las señales lanzan este error
            messages.error(request, getattr(e, "message", str(e)))
            return redirect("cuentas:lista_usuarios")

    # GET → confirmación
    return render(
        request,
        "cuentas/eliminar_usuario.html",
        {"usuario": usuario, "estudiantes": estudiantes_asociados}
    )


# Nueva vista para verificar CI en tiempo real
@role_required("director")
@require_http_methods(["GET"])
def verificar_ci(request):
    ci = request.GET.get("ci", "")
    existe = Usuario.objects.filter(ci=ci).exists()
    return JsonResponse({"existe": existe})
