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

from django.db import transaction
from django.db.models import Q
from django.db.models.deletion import RestrictedError, ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from apps.cuentas.models import Usuario
from apps.cuentas.roles import es_director, total_directores_activos
from apps.cuentas.decorators import role_required

from apps.estudiantes.models.estudiante import Estudiante
from apps.cursos.models import Curso
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
# Imports defensivos (por si cambia ruta de modelos)
try:
    from apps.estudiantes.models.kardex_registro import KardexRegistro
except Exception:
    KardexRegistro = None

try:
    # Intento 1: citaciones/citacion.py con clase Citacion
    from apps.citaciones.models.citacion import Citacion
except Exception:
    try:
        # Intento 2: __init__.py expone Citacion
        from apps.citaciones.models import Citacion
    except Exception:
        Citacion = None

try:
    from apps.estudiantes.models.asistencia_config import AsistenciaCalendario
except Exception:
    AsistenciaCalendario = None


def _es_padre_local(u: Usuario) -> bool:
    return bool(u.rol and (u.rol.nombre or "").strip().lower() == "padre de familia")

@role_required("director")
@require_http_methods(["GET", "POST"])
@transaction.atomic
def eliminar_usuario(request, user_id):
    """
    Dos modos:
    - Seguro (por defecto): NO destruye historial; desvincula y, si hay bloqueos, inactiva.
    - Forzado (eliminar_todo=1): borra dependencias bloqueantes (Citaciones/Kardex/Calendarios) y luego el Usuario.
    """
    usuario = get_object_or_404(Usuario, pk=user_id)

    if request.method == "POST":
        # Seguridad básica
        if getattr(request.user, "pk", None) == usuario.pk:
            messages.error(request, "No puedes eliminar tu propio usuario.")
            return redirect("cuentas:ver_usuario", user_id=usuario.pk)

        if es_director(usuario) and total_directores_activos(exclude_pk=usuario.pk) == 0:
            messages.error(request, "No puedes eliminar al único Director activo.")
            return redirect("cuentas:ver_usuario", user_id=usuario.pk)

        force = request.POST.get("eliminar_todo") in ("1", "true", "True", "on")

        # === MODO FORZADO (destructivo) ===
        if force:
            # 1) Si es Director: eliminar calendarios de asistencia creados por él (PROTECT)
            if AsistenciaCalendario is not None and es_director(usuario):
                AsistenciaCalendario.objects.filter(creado_por=usuario).delete()

            # 2) Estudiantes asociados por ser PADRE o REGENTE
            estudiantes_qs = Estudiante.objects.filter(
                Q(padre=usuario) | Q(curso__regente=usuario)
            ).distinct()

            # 3) Eliminar CITACIONES de esos estudiantes (y citaciones que apunten a sus kardex)
            if estudiantes_qs.exists() and Citacion is not None:
                if KardexRegistro is not None:
                    kdx_qs = KardexRegistro.objects.filter(estudiante__in=estudiantes_qs)
                    # Borrar citaciones por estudiante o por kardex_registro de esos estudiantes
                    Citacion.objects.filter(
                        Q(estudiante__in=estudiantes_qs) | Q(kardex_registro__in=kdx_qs)
                    ).delete()
                else:
                    Citacion.objects.filter(estudiante__in=estudiantes_qs).delete()

            # 4) Eliminar KARDEX de esos estudiantes
            if estudiantes_qs.exists() and KardexRegistro is not None:
                KardexRegistro.objects.filter(estudiante__in=estudiantes_qs).delete()

            # 5) Eliminar ESTUDIANTES asociados
            if estudiantes_qs.exists():
                estudiantes_qs.delete()

            # 6) Cursos donde era REGENTE: soltarlos (no borramos cursos)
            Curso.objects.filter(regente=usuario).update(regente=None)

            # 7) Finalmente, borrar el USUARIO
            usuario.delete()
            messages.success(
                request,
                "Usuario y dependencias asociadas eliminados permanentemente (modo forzado)."
            )
            return redirect("cuentas:lista_padres" if _es_padre_local(usuario) else "cuentas:lista_personal")

        # === MODO SEGURO (por defecto) ===
        # Desvincular sin destruir historial
        Estudiante.objects.filter(padre=usuario).update(padre=None)
        Curso.objects.filter(regente=usuario).update(regente=None)

        if AsistenciaCalendario is not None and es_director(usuario):
            # Mejor intentar re-asignar a quien ejecuta
            if getattr(request.user, "pk", None):
                AsistenciaCalendario.objects.filter(creado_por=usuario).update(creado_por=request.user)

        try:
            usuario.delete()
            messages.success(request, "Usuario eliminado correctamente.")
            return redirect("cuentas:lista_padres" if _es_padre_local(usuario) else "cuentas:lista_personal")
        except (RestrictedError, ProtectedError):
            # Fallback: inactivar
            Usuario.objects.filter(pk=usuario.pk).update(is_activo=False)
            messages.warning(
                request,
                "No se pudo eliminar por dependencias. Se inactivó el usuario para preservar historial."
            )
            return redirect("cuentas:ver_usuario", user_id=usuario.pk)

    # GET: mostrar confirmación con opción de borrado forzado
    n_estudiantes_asociados = Estudiante.objects.filter(
        Q(padre=usuario) | Q(curso__regente=usuario)
    ).distinct().count()
    n_cursos_regente = Curso.objects.filter(regente=usuario).count()
    n_calendarios = 0
    if AsistenciaCalendario is not None:
        n_calendarios = AsistenciaCalendario.objects.filter(creado_por=usuario).count()

    ctx = {
        "usuario": usuario,
        "n_estudiantes_asociados": n_estudiantes_asociados,
        "n_cursos_regente": n_cursos_regente,
        "n_calendarios": n_calendarios,
        "permite_forzado": True,
    }
    return render(request, "cuentas/eliminar_usuario.html", ctx)


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
@role_required("director")
def lista_personal(request):
    """
    Listado de Director, Secretaria(s) y Regentes con filtro de búsqueda.
    """
    query = request.GET.get("q", "").strip()

    usuarios = Usuario.objects.filter(
        rol__nombre__iregex=_PERSONAL_REGEX
    )

    if query:
        usuarios = usuarios.filter(
            Q(rol__nombre__icontains=query) |
            Q(ci__icontains=query) |
            Q(apellidos__icontains=query) |
            Q(nombres__icontains=query)
        )

    usuarios = usuarios.order_by("-id")

    ctx = {
        "usuarios": usuarios,
        "tipo": "personal",
        "titulo": "Usuarios (Personal Administrativo)",
        "query": query,
    }
    return render(request, "cuentas/lista_usuarios.html", ctx)


@role_required("director")
def lista_padres(request):
    """
    Listado de Padres de familia con filtro de búsqueda.
    """
    query = request.GET.get("q", "").strip()

    usuarios = Usuario.objects.filter(
        rol__nombre__iregex=_PADRE_REGEX
    )

    if query:
        usuarios = usuarios.filter(
            Q(rol__nombre__icontains=query) |
            Q(ci__icontains=query) |
            Q(apellidos__icontains=query) |
            Q(nombres__icontains=query)
        )

    usuarios = usuarios.order_by("-id")

    ctx = {
        "usuarios": usuarios,
        "tipo": "padres",
        "titulo": "Usuarios (Padres de familia)",
        "query": query,
    }
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