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
from apps.cursos.models import Curso

from django.db.models import Q

# ======================================
# 🔎 Buscar usuarios (antes lista_usuarios)
# ======================================
@role_required("director")
def buscar_usuarios(request):
    query = request.GET.get("q", "").strip()
    usuarios = Usuario.objects.all().order_by("-id")

    if query:
        usuarios = usuarios.filter(
            Q(rol__nombre__icontains=query) |
            Q(ci__icontains=query) |
            Q(apellidos__icontains=query) |
            Q(nombres__icontains=query)
        )

    context = {
        "usuarios": usuarios,
        "query": query
    }
    return render(request, "cuentas/lista_usuarios.html", context)

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
    Reglas:
    - Autoedición: no puede inactivarse a sí mismo.
    - Último Director activo: no se puede cambiar rol ni inactivar.
    """
    usuario = get_object_or_404(Usuario.objects.select_for_update(), id=user_id)
    es_autoedicion = (usuario.id == request.user.id)

    if request.method == "POST":
        form = UsuarioUpdateForm(request.POST, instance=usuario)

        if es_autoedicion:
            quiere_inactivarse = not bool(request.POST.get("is_activo"))
            if quiere_inactivarse:
                messages.error(request, "No puedes inactivarte a ti mismo.")
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
            es_dir_actual = es_director(usuario)
            es_ultimo_dir = es_dir_actual and total_directores_activos(exclude_pk=usuario.pk) == 0

            nuevo_rol = form.cleaned_data.get("rol") if "rol" in form.cleaned_data else getattr(usuario, "rol", None)
            nuevo_is_activo = form.cleaned_data.get("is_activo", getattr(usuario, "is_activo", True))
            sigue_dir = (getattr(nuevo_rol, "nombre", "") or "").strip().lower() == "director"

            if es_ultimo_dir:
                if not sigue_dir:
                    form.add_error("rol", "No puedes cambiar el rol del único Director activo.")
                    messages.error(request, "No puedes cambiar el rol del único Director activo.")
                    return render(request, "cuentas/editar_usuario.html",
                                  {"form": form, "usuario": usuario, "es_autoedicion": es_autoedicion})
                if not nuevo_is_activo:
                    if "is_activo" in form.fields:
                        form.add_error("is_activo", "No puedes desactivar al único Director activo.")
                    messages.error(request, "No puedes desactivar al único Director activo.")
                    return render(request, "cuentas/editar_usuario.html",
                                  {"form": form, "usuario": usuario, "es_autoedicion": es_autoedicion})

            try:
                form.save()
                messages.success(request, "Usuario actualizado correctamente.")
                return redirect("cuentas:lista_usuarios")
            except ValidationError as e:
                msg = getattr(e, "message", str(e))
                if "Director" in msg or "Director" in str(nuevo_rol):
                    if "rol" in form.fields:
                        form.add_error("rol", msg)
                else:
                    form.add_error(None, msg)
                messages.error(request, msg)
                return render(request, "cuentas/editar_usuario.html",
                              {"form": form, "usuario": usuario, "es_autoedicion": es_autoedicion})
    else:
        form = UsuarioUpdateForm(instance=usuario)
        if es_director(usuario) and total_directores_activos(exclude_pk=usuario.pk) == 0:
            if "rol" in form.fields:
                form.fields["rol"].disabled = True
                form.fields["rol"].help_text = "No puedes cambiar el rol: es el único Director activo."
            if "is_activo" in form.fields:
                form.fields["is_activo"].disabled = True
                form.fields["is_activo"].help_text = "No puedes desactivarlo: es el único Director activo."
        if es_autoedicion and "is_activo" in form.fields:
            form.fields["is_activo"].disabled = True
            form.fields["is_activo"].help_text = "No puedes inactivarte a ti mismo."

    return render(request, "cuentas/editar_usuario.html",
                  {"form": form, "usuario": usuario, "es_autoedicion": es_autoedicion})


@role_required("director")
@require_http_methods(["GET", "POST"])
@transaction.atomic
def eliminar_usuario(request, user_id):
    """
    Elimina un usuario con confirmación.
    Con SET_NULL activo en Curso.regente, los cursos quedarán sin regente automáticamente.
    Si tiene estudiantes asociados como padre, sigue tu confirmación.
    """
    usuario = get_object_or_404(Usuario.objects.select_for_update(), id=user_id)

    if usuario.id == request.user.id:
        messages.error(request, "No puedes eliminarte a ti mismo.")
        return redirect("cuentas:lista_usuarios")

    estudiantes_padre = Estudiante.objects.filter(padre=usuario)
    estudiantes_regente = Estudiante.objects.filter(curso__regente=usuario)
    estudiantes_asociados = (estudiantes_padre | estudiantes_regente).distinct()

    # Solo para feedback: cuántos cursos perderán regente (quedarán en NULL)
    n_cursos = Curso.objects.filter(regente=usuario).count()

    if request.method == "POST":
        try:
            if "eliminar_todo" in request.POST:
                estudiantes_asociados.delete()
                usuario.delete()
                extra = f" {n_cursos} curso(s) quedaron sin regente." if n_cursos else ""
                messages.success(request, f"🗑️ Usuario eliminado junto a sus estudiantes.{extra}")
                return redirect("cuentas:lista_usuarios")

            elif not estudiantes_asociados.exists():
                usuario.delete()
                extra = f" {n_cursos} curso(s) quedaron sin regente." if n_cursos else ""
                messages.success(request, f"🗑️ Usuario eliminado.{extra}")
                return redirect("cuentas:lista_usuarios")

            # Si tenía estudiantes y no se marcó eliminar_todo, no hacer nada especial (tu flujo)
            return redirect("cuentas:lista_usuarios")

        except ValidationError as e:
            messages.error(request, getattr(e, "message", str(e)))
            return redirect("cuentas:lista_usuarios")

    return render(request, "cuentas/eliminar_usuario.html",
                  {"usuario": usuario, "estudiantes": estudiantes_asociados})


# Nueva vista para verificar CI en tiempo real
@role_required("director")
@require_http_methods(["GET"])
def verificar_ci(request):
    ci = request.GET.get("ci", "")
    existe = Usuario.objects.filter(ci=ci).exists()
    return JsonResponse({"existe": existe})

