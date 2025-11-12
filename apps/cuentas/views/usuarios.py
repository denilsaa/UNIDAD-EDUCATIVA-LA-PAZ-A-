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
from apps.cuentas.models import Rol, Usuario
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404, render
from django.views.decorators.http import require_http_methods
from django.db import transaction
from apps.cuentas.roles import es_director, total_directores_activos
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

# Conjuntos de roles permitidos por sección
_PERSONAL_REGEX = r"^(Director|Secretaria|Secretaría|Regente)$"
_PADRE_REGEX = r"^(Padre de familia)$"

def _rol_queryset_personal():
    return Rol.objects.filter(nombre__iregex=_PERSONAL_REGEX).order_by("nombre")

def _rol_queryset_padre():
    return Rol.objects.filter(nombre__iregex=_PADRE_REGEX)

def _es_padre(usuario: Usuario) -> bool:
    return bool(usuario.rol and (usuario.rol.nombre or "").lower().strip() == "padre de familia")

def _es_personal(usuario: Usuario) -> bool:
    return not _es_padre(usuario)

# -------- LISTADOS --------
def lista_personal(request):
    usuarios = Usuario.objects.filter(rol__nombre__iregex=_PERSONAL_REGEX).order_by("-id")
    ctx = {"usuarios": usuarios, "tipo": "personal", "titulo": "Usuarios (Personal Administrativo)"}
    return render(request, "cuentas/lista_usuarios.html", ctx)

def lista_padres(request):
    usuarios = Usuario.objects.filter(rol__nombre__iregex=_PADRE_REGEX).order_by("-id")
    ctx = {"usuarios": usuarios, "tipo": "padres", "titulo": "Usuarios (Padres de familia)"}
    return render(request, "cuentas/lista_usuarios.html", ctx)

# -------- CREACIÓN --------
@require_http_methods(["GET", "POST"])
@transaction.atomic
def crear_personal(request):
    from apps.cuentas.forms import UsuarioCreateForm
    if request.method == "POST":
        form = UsuarioCreateForm(request.POST)
        form.fields["rol"].queryset = _rol_queryset_personal()
        if form.is_valid():
            rol = form.cleaned_data.get("rol")
            if not _rol_queryset_personal().filter(pk=rol.pk).exists():
                messages.error(request, "Rol inválido para Personal.")
            else:
                form.save()
                messages.success(request, "Usuario de personal creado correctamente.")
                return redirect("cuentas:lista_personal")
    else:
        form = UsuarioCreateForm()
        form.fields["rol"].queryset = _rol_queryset_personal()

    ctx = {"form": form, "tipo": "personal", "titulo": "Nuevo usuario (Personal)"}
    return render(request, "cuentas/crear_usuario.html", ctx)

@require_http_methods(["GET", "POST"])
@transaction.atomic
def crear_padre(request):
    from apps.cuentas.forms import UsuarioCreateForm
    padres_qs = _rol_queryset_padre()
    if request.method == "POST":
        form = UsuarioCreateForm(request.POST)
        form.fields["rol"].queryset = padres_qs
        if form.is_valid():
            rol = form.cleaned_data.get("rol")
            if not padres_qs.filter(pk=rol.pk).exists():
                messages.error(request, "Solo se permite 'Padre de familia' en esta sección.")
            else:
                form.save()
                messages.success(request, "Padre de familia creado correctamente.")
                return redirect("cuentas:lista_padres")
    else:
        form = UsuarioCreateForm()
        form.fields["rol"].queryset = padres_qs
        if padres_qs.exists():
            form.initial["rol"] = padres_qs.first().pk

    ctx = {"form": form, "tipo": "padres", "titulo": "Nuevo Padre de familia"}
    return render(request, "cuentas/crear_usuario.html", ctx)

# -------- EDICIÓN --------
@require_http_methods(["GET", "POST"])
@transaction.atomic
def editar_personal(request, user_id: int):
    from apps.cuentas.forms import UsuarioUpdateForm
    usuario = get_object_or_404(Usuario, pk=user_id)

    # Si es Padre, redirige a su sección
    if _es_padre(usuario):
        messages.info(request, "Este usuario es Padre de familia. Edítalo en su sección.")
        return redirect("cuentas:editar_padre", user_id=user_id)

    if request.method == "POST":
        form = UsuarioUpdateForm(request.POST, instance=usuario)
        form.fields["rol"].queryset = _rol_queryset_personal()

        if form.is_valid():
            yo_mismo = (hasattr(request, "user") and getattr(request.user, "pk", None) == usuario.pk)
            nuevo_rol = form.cleaned_data.get("rol")
            nuevo_activo = form.cleaned_data.get("is_activo", True)

            # No puede inactivarse a sí mismo
            if yo_mismo and not nuevo_activo:
                messages.error(request, "No puedes inactivarte a ti mismo.")
                return redirect("cuentas:editar_personal", user_id=user_id)

            # Director único: no se puede quitar rol ni inactivar
            era_director = es_director(usuario)
            sera_director = es_director(Usuario(rol=nuevo_rol))
            if era_director and (not sera_director or not nuevo_activo):
                if total_directores_activos(exclude_pk=usuario.pk) == 0:
                    messages.error(request, "No puedes quitar al único Director activo ni inactivarlo.")
                    return redirect("cuentas:editar_personal", user_id=user_id)

            form.save()
            messages.success(request, "Usuario de personal actualizado correctamente.")
            return redirect("cuentas:lista_personal")
    else:
        form = UsuarioUpdateForm(instance=usuario)
        form.fields["rol"].queryset = _rol_queryset_personal()

    ctx = {"form": form, "usuario": usuario, "tipo": "personal", "titulo": "Editar usuario (Personal)"}
    return render(request, "cuentas/editar_usuario.html", ctx)

@require_http_methods(["GET", "POST"])
@transaction.atomic
def editar_padre(request, user_id: int):
    from apps.cuentas.forms import UsuarioUpdateForm
    usuario = get_object_or_404(Usuario, pk=user_id)

    if _es_personal(usuario):
        messages.info(request, "Este usuario pertenece a Personal. Edítalo en su sección.")
        return redirect("cuentas:editar_personal", user_id=user_id)

    padres_qs = _rol_queryset_padre()

    if request.method == "POST":
        form = UsuarioUpdateForm(request.POST, instance=usuario)
        form.fields["rol"].queryset = padres_qs
        if form.is_valid():
            nuevo_rol = form.cleaned_data.get("rol")
            if not padres_qs.filter(pk=nuevo_rol.pk).exists():
                messages.error(request, "Solo se permite el rol 'Padre de familia' en esta sección.")
                return redirect("cuentas:editar_padre", user_id=user_id)

            form.save()
            messages.success(request, "Padre de familia actualizado correctamente.")
            return redirect("cuentas:lista_padres")
    else:
        form = UsuarioUpdateForm(instance=usuario)
        form.fields["rol"].queryset = padres_qs

    ctx = {"form": form, "usuario": usuario, "tipo": "padres", "titulo": "Editar usuario (Padre de familia)"}
    return render(request, "cuentas/editar_usuario.html", ctx)