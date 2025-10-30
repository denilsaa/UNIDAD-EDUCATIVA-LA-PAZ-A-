# apps/cuentas/views/usuarios.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.apps import apps as django_apps

from apps.cuentas.models import Usuario
from apps.cuentas.forms import UsuarioCreateForm, UsuarioUpdateForm

# 🔒 Decorador que exige login y rol == director
from apps.cuentas.decorators import role_required
from apps.cuentas.roles import es_director, total_directores_activos
from apps.estudiantes.models.estudiante import Estudiante
from apps.cursos.models import Curso

# ==== Centinela (coincidir con cursos/views) ====
SENT_REGENTE_EMAIL = "sin.regente@ue-lapaz.internal"
SENT_NOMBRES = "SIN"
SENT_APELLIDOS = "REGENTE"

def _ensure_regente_role():
    Rol = django_apps.get_model("cuentas", "Rol")
    rol = Rol.objects.filter(nombre__iexact="Regente").first()
    if not rol:
        rol = Rol.objects.create(nombre="Regente")
    return rol

def _is_regente_centinela(u: Usuario) -> bool:
    try:
        if not isinstance(u, Usuario):
            return False
        if (u.email or "").lower() == SENT_REGENTE_EMAIL:
            return True
        # fallback por nombre/apellido/inactivo/rol
        rol_nombre = (getattr(getattr(u, "rol", None), "nombre", "") or "").strip().lower()
        return (
            (u.nombres or "").strip().upper() == SENT_NOMBRES and
            (u.apellidos or "").strip().upper() == SENT_APELLIDOS and
            rol_nombre == "regente" and
            not bool(getattr(u, "is_activo", True))
        )
    except Exception:
        return False

def _get_or_create_regente_sin_regente():
    UsuarioModel = django_apps.get_model("cuentas", "Usuario")
    rol_regente = _ensure_regente_role()

    obj = UsuarioModel.objects.filter(email=SENT_REGENTE_EMAIL).first()
    if obj:
        if getattr(obj, "rol_id", None) != rol_regente.id:
            obj.rol = rol_regente
            obj.save(update_fields=["rol"])
        return obj

    defaults = {
        "nombres": SENT_NOMBRES,
        "apellidos": SENT_APELLIDOS,
        "is_activo": False,
        "rol": rol_regente,
    }
    for fname, fval in [("ci", "SIN-REGENTE-000"), ("username", "sin_regente")]:
        try:
            field = UsuarioModel._meta.get_field(fname)
            if not field.null:
                defaults[fname] = fval
        except Exception:
            pass
    try:
        UsuarioModel._meta.get_field("password")
        defaults.setdefault("password", "!")
    except Exception:
        pass

    obj, _ = UsuarioModel.objects.get_or_create(email=SENT_REGENTE_EMAIL, defaults=defaults)
    return obj


@role_required("director")
def lista_usuarios(request):
    # Ocultar el usuario centinela en la lista
    usuarios = (
        Usuario.objects
        .exclude(email=SENT_REGENTE_EMAIL)
        .order_by("-id")
    )
    return render(request, "cuentas/lista_usuarios.html", {"usuarios": usuarios})


@role_required("director")
def ver_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    if _is_regente_centinela(usuario):
        messages.info(request, "El usuario ‘SIN REGENTE’ es de sistema y no se muestra.")
        return redirect("cuentas:lista_usuarios")
    return render(request, "cuentas/ver_usuario.html", {"usuario": usuario})


@role_required("director")
@require_http_methods(["GET", "POST"])
def crear_usuario(request):
    if request.method == "POST":
        form = UsuarioCreateForm(request.POST)
        if form.is_valid():
            try:
                # Evitar crear accidentalmente un email igual al centinela
                if (form.cleaned_data.get("email") or "").lower() == SENT_REGENTE_EMAIL:
                    form.add_error("email", "Ese correo está reservado por el sistema.")
                    return render(request, "cuentas/crear_usuario.html", {"form": form})
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
    - No se puede editar el usuario centinela.
    - Autoedición: no puede inactivarse a sí mismo.
    - Último Director activo: no se puede cambiar rol ni inactivar.
    """
    usuario = get_object_or_404(Usuario.objects.select_for_update(), id=user_id)

    # Bloquear edición del centinela
    if _is_regente_centinela(usuario):
        messages.error(request, "El usuario ‘SIN REGENTE’ es de sistema y no se puede editar.")
        return redirect("cuentas:lista_usuarios")

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
                    request, "cuentas/editar_usuario.html",
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
    - No se puede eliminar el usuario centinela ‘SIN REGENTE’.
    - Antes de eliminar un regente normal, sus cursos pasan al centinela.
    - Se respeta tu lógica de estudiantes asociados.
    """
    usuario = get_object_or_404(Usuario.objects.select_for_update(), id=user_id)

    # Bloquear eliminación del centinela
    if _is_regente_centinela(usuario):
        messages.error(request, "El usuario ‘SIN REGENTE’ es de sistema y no se puede eliminar.")
        return redirect("cuentas:lista_usuarios")

    if usuario.id == request.user.id:
        messages.error(request, "No puedes eliminarte a ti mismo.")
        return redirect("cuentas:lista_usuarios")

    estudiantes_padre = Estudiante.objects.filter(padre=usuario)
    estudiantes_regente = Estudiante.objects.filter(curso__regente=usuario)
    estudiantes_asociados = (estudiantes_padre | estudiantes_regente).distinct()

    cursos_qs = Curso.objects.filter(regente=usuario)

    if request.method == "POST":
        if usuario.id == request.user.id:
            messages.error(request, "No puedes eliminarte a ti mismo.")
            return redirect("cuentas:lista_usuarios")

        try:
            # Reasignar cursos a centinela si era regente
            n_cursos = cursos_qs.count()
            if n_cursos:
                centinela = _get_or_create_regente_sin_regente()
                cursos_qs.update(regente=centinela)

            if "eliminar_todo" in request.POST:
                estudiantes_asociados.delete()
                usuario.delete()
                messages.success(request, f"🗑️ El usuario {usuario} y sus estudiantes fueron eliminados.")
                return redirect("cuentas:lista_usuarios")

            elif not estudiantes_asociados.exists():
                usuario.delete()
                msg_ok = f"🗑️ El usuario {usuario} fue eliminado."
                if n_cursos:
                    msg_ok += f" {n_cursos} curso(s) quedaron con ‘SIN REGENTE’."
                messages.success(request, msg_ok)
                return redirect("cuentas:lista_usuarios")

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
